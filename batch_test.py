from utils.dify_client_v2 import DifyClient
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import tkinter as tk
from tkinter import messagebox
from time import sleep
import logging
import os

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def setup_dify_client():
    """初始化Dify客户端"""
    try:
        # 建议从环境变量获取API密钥，提高安全性
        api_key = os.getenv("DIFY_API_KEY", "Dify工作流的api-key")
        return DifyClient(api_key=api_key)
    except Exception as e:
        logger.error(f"初始化Dify客户端失败: {str(e)}")
        raise


def chat(query, client=None, max_retries=3):
    """与Dify API进行对话，包含重试机制"""
    for attempt in range(max_retries):
        try:
            if client is None:
                client = setup_dify_client()

            result = client.run_chat(query, "dify-user")

            # 直接处理字典，避免不必要的JSON序列化和反序列化
            if isinstance(result, str):
                result = json.loads(result)

            answer = result.get("answer", "")

            # 如果获取到有效答案，立即返回
            if False and  answer and answer.strip():
                return query, answer, True

            # 如果答案为空，也视为失败，需要重试
            logger.warning(f"第 {attempt + 1} 次尝试获取到空答案，查询: '{query}'")

        except Exception as e:
            logger.warning(f"第 {attempt + 1} 次尝试处理查询 '{query}' 时出错: {str(e)}")

        # 如果不是最后一次尝试，则等待一段时间后重试
        if attempt < max_retries - 1:
            sleep_time = 2 ** attempt  # 指数退避策略
            logger.info(f"等待 {sleep_time} 秒后重试...")
            sleep(sleep_time)

    # 所有重试都失败
    logger.error(f"所有 {max_retries} 次尝试都失败，查询: '{query}'")
    return query, "", False


def thread_chat(query_list, max_workers=10):
    """多线程处理查询"""
    error_info = {}
    client = setup_dify_client()  # 预先初始化客户端

    # 创建进度条
    pbar = tqdm(total=len(query_list), desc="处理进度", unit="query")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务，传递已初始化的客户端
        future_to_query = {
            executor.submit(chat, query, client): query
            for query in query_list
        }

        # 使用as_completed来获取已完成的任务
        for future in as_completed(future_to_query):
            query = future_to_query[future]
            try:
                q, r, success = future.result()
                pbar.update(1)

                if success:
                    pbar.set_postfix(状态="成功", 当前处理=f"'{q[:20]}...'" if len(q) > 20 else f"'{q}'")
                    yield q, r, True
                else:
                    error_info[query] = "所有重试均失败"
                    pbar.set_postfix(状态="失败", 当前处理=f"'{q[:20]}...'" if len(q) > 20 else f"'{q}'")
                    yield query, "", False

            except Exception as e:
                error_info[query] = f"线程执行错误: {str(e)}"
                pbar.update(1)
                pbar.set_postfix(状态="异常", 当前处理=f"'{query[:20]}...'" if len(query) > 20 else f"'{query}'")
                yield query, "", False

    # 关闭进度条
    pbar.close()

    # 记录错误信息
    if error_info:
        logger.error(f"处理过程中出现 {len(error_info)} 个错误")
        for query, error in error_info.items():
            logger.error(f"查询: {query}, 错误: {error}")


def read_txt(file_path):
    """读取txt文件，返回过滤后的列表"""
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件 {file_path} 不存在")

        with open(file_path, "r", encoding="utf-8") as f:
            # 过滤空行和只包含空白字符的行
            query_list = [
                line.strip() for line in f.readlines()
                if line.strip()
            ]

        if not query_list:
            raise ValueError("文件为空或只包含空行")

        logger.info(f"从 {file_path} 读取了 {len(query_list)} 个有效查询")
        return query_list

    except Exception as e:
        logger.error(f"读取文件失败: {str(e)}")
        raise


def write_result(query, answer, file_handle):
    """将结果写入文件"""
    try:
        file_handle.write(f"query: {query}\n")
        # 保留换行符，但确保格式整洁
        formatted_answer = answer.replace("\n", "")  # 或者保留原格式
        formatted_answer = formatted_answer.replace(" ", "")
        file_handle.write(f"answer: {formatted_answer}\n")
        file_handle.write("-" * 50 + "\n")  # 添加分隔线
        file_handle.flush()
        return True
    except Exception as e:
        logger.error(f"写入结果失败: {str(e)}")
        return False


def show_completion_notification(total_queries, success_count):
    """显示完成通知"""
    try:
        root = tk.Tk()
        root.withdraw()
        message = f"所有查询处理完成！\n共处理了 {total_queries} 个查询\n成功: {success_count} 个\n失败: {total_queries - success_count} 个\n结果已保存到 result.txt"
        messagebox.showinfo("处理完成", message)
        root.destroy()
    except Exception as e:
        # 如果GUI不可用，则在控制台显示
        logger.info(f"GUI通知失败，使用控制台输出: {str(e)}")
        print(f"处理完成！总共: {total_queries}, 成功: {success_count}, 失败: {total_queries - success_count}")


def main():
    """主函数"""
    try:
        # 1. 读取txt文件
        query_list = read_txt("query.txt")
        print(f"共有 {len(query_list)} 个问题需要处理")

        # 2. 多线程处理
        error_query_list = []
        success_count = 0

        with open("result.txt", "w", encoding="utf-8") as f:
            # 写入文件头
            f.write(f"处理时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"总查询数: {len(query_list)}\n")
            f.write("=" * 50 + "\n")

            # 遍历生成器，有结果就立即写入文件
            for q, r, success in thread_chat(query_list):
                if success and r:
                    if write_result(q, r, f):
                        success_count += 1
                    else:
                        error_query_list.append(q)
                else:
                    error_query_list.append(q)

        # 3. 如果还有失败的问题，记录到单独文件
        if error_query_list:
            error_file = "failed_queries.txt"
            with open(error_file, "w", encoding="utf-8") as f:
                f.write(f"失败查询列表 - 共 {len(error_query_list)} 个\n")
                f.write("=" * 50 + "\n")
                for query in error_query_list:
                    f.write(query + "\n")
            logger.warning(f"有 {len(error_query_list)} 个查询失败，已保存到 {error_file}")

        # 4. 显示完成通知
        show_completion_notification(len(query_list), success_count)

    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}")
        # 显示错误通知
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("错误", f"程序执行过程中出现错误:\n{str(e)}")
            root.destroy()
        except:
            print(f"错误: {str(e)}")


if __name__ == "__main__":
    main()