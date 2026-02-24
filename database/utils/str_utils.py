import re


def camel_to_snake(camel_str):
    """
    将大驼峰字符串转换为下划线分割字符串
    :param camel_str: 大驼峰格式字符串（如 "CamelCase"、"UserName"）
    :return: 下划线分割格式字符串（如 "camel_case"、"user_name"）
    """
    # 1. 匹配“大写字母”前的位置，插入下划线（处理首字母外的大写）
    # (?=[A-Z]) 是正向查找，表示“后面紧跟大写字母”的位置
    snake_str = re.sub(r"(?=[A-Z])", "_", camel_str)
    # 2. 统一转为小写（处理首字母大写）
    snake_str = snake_str.lower()
    # 3. 移除可能出现在字符串开头的下划线（如输入 "CamelCase" 第一步会变成 "_camel_case"）
    return snake_str.lstrip("_")
