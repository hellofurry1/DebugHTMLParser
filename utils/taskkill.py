import subprocess
import psutil
import logging
# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='log.log',  # 日志文件名
    filemode='w',
    encoding='utf-8'  # 日志文件编码
)


def kill_process():
    try:
        logging.info(f"开始结束所有MicrosoftEdge.exe进程")
        task_list = psutil.process_iter()
        for task in task_list:
            if task.name() in ("msedge.exe", "MicrosoftEdge.exe"):
                pid = task.pid
                logging.info(f"结束进程: {pid}")
                # 执行结束进程命令并捕获输出
                result = subprocess.run(f"taskkill /PID {pid} /F", shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    logging.info(f"结束进程 {pid} 成功，输出: {result.stdout.strip()}")
                else:
                    logging.error(f"结束进程 {pid} 失败，错误信息: {result.stderr.strip()}")

        logging.info("结束所有MicrosoftEdge.exe进程")

        # 启动浏览器并捕获输出
        start_result = subprocess.run(r"start msedge.exe --remote-debugging-port=9222 --remote-allow-origins=*", shell=True, capture_output=True, text=True)
        if start_result.returncode == 0:
            logging.info(f"启动Microsoft Edge浏览器并开启远程调试成功.")
        else:
            logging.error(f"启动Microsoft Edge浏览器并开启远程调试失败，错误信息: {start_result.stderr.strip()}")
    except Exception as e:
        logging.error(f"执行过程中发生错误: {str(e)}")


if __name__ == "__main__":
    kill_process()
