import time
from dataclasses import dataclass
from ..models.dataclasses import SnowflakeInfo
from .timezone import TimeZone, DEFAULT_FORMAT


@dataclass(frozen=True)
class SnowflakeConfig:
    """雪花算法配置类"""

    # 位分配 - 调整为53位以内以避免JavaScript精度问题
    WORKER_ID_BITS: int = 3
    DATACENTER_ID_BITS: int = 3
    SEQUENCE_BITS: int = 10
    TIMESTAMP_BITS: int = 37  # 时间戳位数（37位可表示约137年）

    # 最大值
    MAX_WORKER_ID: int = (1 << WORKER_ID_BITS) - 1  # 31
    MAX_DATACENTER_ID: int = (1 << DATACENTER_ID_BITS) - 1  # 31
    SEQUENCE_MASK: int = (1 << SEQUENCE_BITS) - 1  # 4095

    # 位移偏移
    WORKER_ID_SHIFT: int = SEQUENCE_BITS
    DATACENTER_ID_SHIFT: int = SEQUENCE_BITS + WORKER_ID_BITS
    TIMESTAMP_LEFT_SHIFT: int = SEQUENCE_BITS + WORKER_ID_BITS + DATACENTER_ID_BITS

    # 元年时间戳（2025-01-01 00:00:00）- 较新的起始时间可减少时间戳位数占用
    EPOCH: int = 1735660800000

    # 总位数校验（关键修复：确保总位数 ≤ 53）
    TOTAL_BITS: int = (
        TIMESTAMP_BITS + DATACENTER_ID_BITS + WORKER_ID_BITS + SEQUENCE_BITS
    )
    assert TOTAL_BITS <= 53, f"总位数({TOTAL_BITS})超过53位，会导致JavaScript精度丢失"

    # 默认值
    DEFAULT_DATACENTER_ID: int = 1
    DEFAULT_WORKER_ID: int = 0
    DEFAULT_SEQUENCE: int = 0


# 1. 雪花 ID 生成器（简化版，生产环境需完善机器 ID 分配和时钟回拨处理）
class Snowflake:
    "雪花算法"

    def __init__(
        self,
        cluster_id: int = SnowflakeConfig.DEFAULT_DATACENTER_ID,
        node_id: int = SnowflakeConfig.DEFAULT_WORKER_ID,
        sequence: int = SnowflakeConfig.DEFAULT_SEQUENCE,
    ):
        """
        初始化雪花算法生成器

        :param cluster_id: 集群 ID (0-31)
        :param node_id: 节点 ID (0-31)
        :param sequence: 起始序列号
        """
        if cluster_id < 0 or cluster_id > SnowflakeConfig.MAX_DATACENTER_ID:
            raise errors.RequestError(
                msg=f"集群编号必须在 0-{SnowflakeConfig.MAX_DATACENTER_ID} 之间"
            )
        if node_id < 0 or node_id > SnowflakeConfig.MAX_WORKER_ID:
            raise errors.RequestError(
                msg=f"节点编号必须在 0-{SnowflakeConfig.MAX_WORKER_ID} 之间"
            )

        self.node_id = node_id
        self.cluster_id = cluster_id
        self.sequence = sequence
        self.last_timestamp = -1

    @classmethod
    def generate_id(self):
        timestamp = int(time.time() * 1000)
        # 处理时钟回拨
        if timestamp < self.last_timestamp:
            raise Exception(f"时钟回拨：{self.last_timestamp - timestamp} 毫秒")
        # 同一毫秒内，序列号自增
        if timestamp == self.last_timestamp:
            self.sequence = (self.sequence + 1) & 4095  # 4095 = 2^12 - 1
            if self.sequence == 0:
                # 序列号用尽，等待下一毫秒
                timestamp = self._wait_next_millisecond(self.last_timestamp)
        else:
            self.sequence = 0  # 新的毫秒，序列号重置
        self.last_timestamp = timestamp

        # 雪花 ID 结构：时间戳（41位）+ 数据中心 ID（5位）+ 机器 ID（5位）+ 序列号（12位）
        snowflake_id = (
            (timestamp << 22)
            | (self.cluster_id << 17)
            | (self.node_id << 12)
            | self.sequence
        )
        return snowflake_id

    @staticmethod
    def _current_millis() -> int:
        """返回当前毫秒时间戳"""
        return int(time.time() * 1000)

    def _next_millis(self, last_timestamp: int) -> int:
        """
        等待至下一毫秒

        :param last_timestamp: 上次生成 ID 的时间戳
        :return:
        """
        timestamp = self._current_millis()
        while timestamp <= last_timestamp:
            time.sleep((last_timestamp - timestamp + 1) / 1000.0)
            timestamp = self._current_millis()
        return timestamp

    def generate(self) -> int:
        """生成雪花ID（确保在53位安全范围内）"""
        timestamp = self._current_millis()

        # 处理时钟回拨
        if timestamp < self.last_timestamp:
            raise ValueError(
                msg=f"系统时间倒退，拒绝生成ID，需等待至 {self.last_timestamp}"
            )

        # 处理同一毫秒内的序列号
        if timestamp == self.last_timestamp:
            self.sequence = (self.sequence + 1) & SnowflakeConfig.SEQUENCE_MASK
            if self.sequence == 0:  # 序列号用尽，等待下一毫秒
                timestamp = self._next_millis(self.last_timestamp)
        else:
            self.sequence = 0  # 新毫秒重置序列号

        self.last_timestamp = timestamp

        # 计算相对时间戳（减少位数占用）
        relative_timestamp = timestamp - SnowflakeConfig.EPOCH

        # 校验时间戳是否超出分配的位数（关键修复）
        if relative_timestamp >= (1 << SnowflakeConfig.TIMESTAMP_BITS):
            raise ValueError("雪花ID时间戳超出最大范围，需调整EPOCH或增加时间戳位数")

        # 生成雪花ID
        snowflake_id = (
            (relative_timestamp << SnowflakeConfig.TIMESTAMP_LEFT_SHIFT)
            | (self.cluster_id << SnowflakeConfig.DATACENTER_ID_SHIFT)
            | (self.node_id << SnowflakeConfig.WORKER_ID_SHIFT)
            | self.sequence
        )

        # 最终安全校验（关键修复）
        if snowflake_id >= (1 << 53):
            raise ValueError(f"生成的雪花ID({snowflake_id})超出JavaScript安全整数范围")

        return snowflake_id

    @staticmethod
    def parse_id(snowflake_id: int) -> SnowflakeInfo:
        """
        解析雪花 ID，获取其包含的详细信息

        :param snowflake_id: 雪花ID
        :return:
        """
        timestamp = (
            snowflake_id >> SnowflakeConfig.TIMESTAMP_LEFT_SHIFT
        ) + SnowflakeConfig.EPOCH
        cluster_id = (
            snowflake_id >> SnowflakeConfig.DATACENTER_ID_SHIFT
        ) & SnowflakeConfig.MAX_DATACENTER_ID
        node_id = (
            snowflake_id >> SnowflakeConfig.WORKER_ID_SHIFT
        ) & SnowflakeConfig.MAX_WORKER_ID
        sequence = snowflake_id & SnowflakeConfig.SEQUENCE_MASK

        return SnowflakeInfo(
            timestamp=timestamp,
            datetime=time.strftime(DEFAULT_FORMAT, time.localtime(timestamp / 1000)),
            cluster_id=cluster_id,
            node_id=node_id,
            sequence=sequence,
        )


snowflake = Snowflake()
