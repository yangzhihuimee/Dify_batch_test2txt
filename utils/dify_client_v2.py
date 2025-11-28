import requests
import json
from io import BytesIO
import mimetypes
import os


class DifyClient:
    def __init__(self, api_key, base_url="https://dify.你的域名.com"):
        """
        初始化 Dify 客户端

        Args:
            api_key (str): API 密钥
            base_url (str, optional): Dify 基础URL.
        """
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
        }

    def upload_file(self, file_path=None, content=None, filename=None, user=None, file_type="TXT"):
        """
        上传文件到 Dify，支持通过文件路径或文件内容上传

        Args:
            file_path (str, optional): 要上传的文件路径. 默认为 None
            content (str, optional): 要上传的文件内容字符串. 默认为 None
            filename (str, optional): 上传的文件名（当使用content时必需）. 默认为 None
            user (str): 用户标识
            file_type (str, optional): 文件类型. 默认为 "TXT"

        Returns:
            str or None: 上传成功返回文件ID，失败返回None
        """
        upload_url = f"{self.base_url}/v1/files/upload"

        # 验证参数
        if file_path is None and content is None:
            raise ValueError("必须提供 file_path 或 content 参数")
        if file_path is not None and content is not None:
            raise ValueError("不能同时提供 file_path 和 content 参数")
        if content is not None and filename is None:
            raise ValueError("使用 content 参数时必须提供 filename")

        try:
            # 处理文件路径上传
            if file_path is not None:
                filename = filename or os.path.basename(file_path)
                mime_type, _ = mimetypes.guess_type(file_path)
                mime_type = mime_type or 'text/plain'

                with open(file_path, 'rb') as file:
                    file_data = file.read()

            # 处理内容上传
            else:
                mime_type = 'text/plain'
                file_data = content.encode('utf-8')

            # 准备上传数据
            files = {
                'file': (filename, BytesIO(file_data), mime_type)
            }
            data = {
                "user": user,
                "type": file_type
            }

            response = requests.post(upload_url, headers=self.headers, files=files, data=data)
            if response.status_code == 201:  # 201 表示创建成功
                return response.json().get("id")  # 获取上传的文件 ID
            else:
                print(f"文件上传失败，状态码: {response.status_code}, 错误信息: {response.text}")
                return None
        except Exception as e:
            print(f"发生错误: {str(e)}")
            return None

    def run_workflow(self, file_id, user, work_type, response_mode="blocking"):
        """
        运行工作流

        Args:
            file_id (str): 文件ID
            user (str): 用户标识
            work_type (str): 工作类型/查询内容
            response_mode (str, optional): 响应模式. 默认为 "blocking"

        Returns:
            dict: 工作流执行结果
        """
        workflow_url = f"{self.base_url}/v1/workflows/run"
        headers = {
            **self.headers,
            "Content-Type": "application/json"
        }

        data = {
            "inputs": {
                "query": work_type,
                "file": {
                    "transfer_method": "local_file",
                    "upload_file_id": file_id,
                    "type": "document"
                }
            },
            "response_mode": response_mode,
            "user": user
        }

        try:
            response = requests.post(workflow_url, headers=headers, json=data, timeout=600)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"工作流执行失败，状态码: {response.status_code}")
                return {"status": "error",
                        "message": f"Failed to execute workflow, status code: {response.status_code}"}
        except Exception as e:
            print(f"发生错误: {str(e)}")
            return {"status": "error", "message": str(e)}

    def run_chat(self, query, user="dify-user", response_mode="blocking"):
        """
        运行工作流

        Args:
            query (str): 用户问题
            user (str): 用户标识
            response_mode (str, optional): 响应模式. 默认为 "blocking"

        Returns:
            dict: 工作流执行结果
        """
        workflow_url = f"{self.base_url}/v1/chat-messages"
        headers = {
            **self.headers,
            "Content-Type": "application/json"
        }

        data = {
            "inputs": {
                # 入参
            },
            "query": query,
            "response_mode": response_mode,
            "user": user
        }

        try:
            response = requests.post(workflow_url, headers=headers, json=data, timeout=600)
            if response.status_code == 200:
                return response.json()
            else:
                # print(f"工作流执行失败，状态码: {response.status_code}; 错误信息: {response.text}; 请求数据: {query}")
                return {"status": "error",
                        "message": f"Failed to execute workflow, status code: {response.status_code}"}
        except Exception as e:
            # print(f"工作流执行失败，错误信息: {str(e)}; 请求数据: {query}")
            return {"status": "error", "message": str(e)}


# 使用示例
if __name__ == "__main__":
    pass