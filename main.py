import sqlite3
from prettytable import PrettyTable
import os

def get_db_connection():
    """创建并返回SQLite数据库连接"""
    try:        # 获取当前脚本文件所在目录（无论是 .py 还是 .exe）
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, 'database.sqlite')
        conn = sqlite3.connect(db_path)  # SQLite database file
        conn.row_factory = sqlite3.Row  # Enable accessing columns by name
        return conn
    except sqlite3.Error as e:
        print(f"数据库连接失败: {e}")
        return None

def get_all_formulas():
    """查询所有水培配方信息"""
    query = "SELECT id, name FROM hydroponic_formulas"
    try:
        conn = get_db_connection()
        if not conn:
            return []
        cursor = conn.cursor()
        cursor.execute(query)
        res = cursor.fetchall()
        formulas = [{"id": row['id'], "name": row['name'] or ""} for row in res]
        cursor.close()
        conn.close()
        return formulas
    except sqlite3.Error as e:
        print(f"数据库查询失败: {e}")
        return []

def get_formula_chemicals(formula_id):
    """查询指定配方包含的化合物及其浓度"""
    query = """
    SELECT c.id, c.name, c.chem, c.ABC, fc.concentration
    FROM formula_chemicals fc
    JOIN chemicals c ON fc.chemical_id = c.id
    WHERE fc.formula_id = ?
    ORDER BY c.ABC
    """
    try:
        conn = get_db_connection()
        if not conn:
            return []
        cursor = conn.cursor()
        cursor.execute(query, (formula_id,))
        res = cursor.fetchall()
        chemicals = [{
            "chemical_id": row['id'],
            "name": row['name'] or "",
            "chemical_formula": row['chem'] or "",
            "category": row['ABC'] or "",
            "concentration": row['concentration'] if row['concentration'] is not None else 0.0
        } for row in res]
        cursor.close()
        conn.close()
        return chemicals
    except sqlite3.Error as e:
        print(f"查询配方化合物失败: {e}")
        return []

def display_formulas(formulas):
    """格式化显示所有配方信息"""
    if not formulas:
        print("没有查询到配方数据")
        return
    print("\n水培配方列表:")
    print("ID\t名称")
    print("-" * 30)
    for formula in formulas:
        print(f"{formula['id']}\t{formula['name']:<12}")

def get_valid_formula_id(formulas):
    """获取用户输入的配方 ID，确保输入有效"""
    formula_ids = [str(formula['id']) for formula in formulas]
    while True:
        display_formulas(formulas)
        user_input = input("\n请输入需要查看的配方 ID（输入 'q' 退出）: ").strip()
        if user_input.lower() == 'q':
            print("程序退出")
            return None
        if user_input in formula_ids:
            return int(user_input)
        print(f"无效 ID，请输入以下 ID 之一: {', '.join(formula_ids)}")

def get_valid_float(prompt, min_value=0.0):
    """获取用户输入的浮点数（体积或稀释倍数），确保输入有效"""
    while True:
        user_input = input(prompt).strip()
        try:
            value = float(user_input)
            if value < min_value:
                print(f"输入必须大于或等于 {min_value}")
                continue
            return value
        except ValueError:
            print("请输入有效的数字")

def process_formula(formula_id, volume_l, dilution_factor, formulas):
    """处理用户输入的配方 ID、体积和稀释倍数，计算每种化合物的质量"""
    selected_formula = next((f for f in formulas if f['id'] == formula_id), None)
    if not selected_formula:
        return f"错误：未找到 ID 为 {formula_id} 的配方"

    chemicals = get_formula_chemicals(formula_id)
    if not chemicals:
        return f"错误：配方 ID {formula_id} 未关联任何化合物"

    # 配方信息
    result = (
        f"\n处理结果：\n"
        f"配方 ID: {selected_formula['id']}\n"
        f"配方名称: {selected_formula['name']}\n"
        f"输入体积: {volume_l:.2f} L\n"
        f"稀释倍数: {dilution_factor:.2f}x\n"
        f"\n所需化合物：\n"
    )

    # 使用 PrettyTable 输出表格
    table = PrettyTable()
    table.field_names = ["分类", "名称", "化学式", "浓度(mg/L)", "质量(g)", "母液"]
    table.align = "l"  # 左对齐
    table.float_format = ".4"  # 浮点数保留 4 位小数

    for chemical in chemicals:
        mass = chemical['concentration'] * volume_l * dilution_factor / 1000  # mg/L * L * 倍数 / 1000 = g
        is_stock_solution = dilution_factor > 1
        stock_solution = "是" if is_stock_solution else "否"
        formula_display = chemical['chemical_formula'] or "-"
        table.add_row([
            chemical['category'],
            chemical['name'],
            formula_display,
            f"{chemical['concentration']:.2f}",
            f"{mass:.4f}",
            stock_solution
        ])

    result += str(table) + "\n"
    return result

def main():
    """主函数，协调程序流程"""
    all_formulas = get_all_formulas()
    if not all_formulas:
        print("无法继续：没有查询到配方数据")
        input("按 Enter 键退出...")  # 确保这里也暂停
        return

    try:
        # 选择配方
        formula_id = get_valid_formula_id(all_formulas)
        if formula_id is None:
            return

        # 输入体积（单位固定为 L）
        volume_l = get_valid_float("请输入体积（L，需大于 0）: ", min_value=0.0001)

        # 输入稀释倍数
        dilution_factor = get_valid_float("请输入稀释倍数（例如 1 表示直接配制，10 表示 10x 母液，需大于 0）: ", min_value=0.0001)

        # 处理配方
        result = process_formula(formula_id, volume_l, dilution_factor, all_formulas)
        print(result)

    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序发生错误: {e}")
    finally:
        print("程序已结束。")
        input("按 Enter 键退出...")

if __name__ == "__main__":
    main()