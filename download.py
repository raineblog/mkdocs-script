import sys
import os
from collections import deque

from PySide6.QtCore import QCoreApplication, QUrl, Slot, QMarginsF
from PySide6.QtGui import QPageLayout, QPageSize
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView

class ConversionManager:
    """
    在主线程中管理多个网页到PDF的转换任务。
    利用Qt的事件循环实现异步并发。
    """
    def __init__(self, url_list, max_concurrent_jobs: int = 8):
        """
        初始化转换管理器。

        Args:
            url_list (List[Tuple[str, str]]): 一个包含 (URL, 输出文件名) 元组的列表。
            max_concurrent_jobs (int): 最大并发任务数。
        """
        self.tasks = deque(url_list)  # 使用双端队列，方便地从左侧弹出任务
        self.max_concurrent_jobs = max_concurrent_jobs
        self.active_jobs = 0
        self.active_views = [] # 持有对视图的引用，防止被垃圾回收

        # 定义页面布局和边距 (单位: 毫米)
        margins = QMarginsF(19, 25.5, 19, 25.5)
        self.page_layout = QPageLayout(
            QPageSize(QPageSize.PageSizeId.A4),
            QPageLayout.Orientation.Portrait,
            margins,
            QPageLayout.Unit.Millimeter,
        )
        print(f"任务管理器已初始化，共有 {len(self.tasks)} 个任务，最大并发数: {self.max_concurrent_jobs}")

    def start(self):
        """
        开始处理任务队列。
        """
        # 初始启动一批任务，直到达到最大并发数
        for _ in range(min(self.max_concurrent_jobs, len(self.tasks))):
            self._start_next_task()

    def _start_next_task(self):
        """
        从队列中取出一个任务并开始执行。
        """
        if not self.tasks:
            return  # 队列已空

        url, output_path = self.tasks.popleft()
        self.active_jobs += 1
        
        print(f"开始处理: {url} -> {output_path} (当前活动任务: {self.active_jobs})")

        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 所有的GUI对象都在主线程中创建
        view = QWebEngineView()
        self.active_views.append(view)

        # 1. 修正 Attribute Error: 使用 PrintElementBackgrounds
        view.settings().setAttribute(
            QWebEngineSettings.WebAttribute.PrintElementBackgrounds, True
        )

        # 使用 lambda 传递额外参数给槽函数
        view.loadFinished.connect(
            lambda ok, v=view, path=output_path: self._on_load_finished(ok, v, path)
        )
        view.load(QUrl(url))
        
    @Slot(bool, QWebEngineView, str)
    def _on_load_finished(self, success: bool, view: QWebEngineView, output_path: str):
        """
        页面加载完成后的槽函数。
        """
        if success:
            print(f"页面加载成功: {view.url().toString()}")
            view.page().pdfPrintingFinished.connect(
                lambda path, ok, v=view: self._on_pdf_printed(path, ok, v)
            )
            view.page().printToPdf(output_path, self.page_layout)
        else:
            print(f"页面加载失败: {view.url().toString()}")
            # 即使失败，也要减少活动任务计数并尝试下一个
            self._task_finished(view)

    @Slot(str, bool, QWebEngineView)
    def _on_pdf_printed(self, file_path: str, success: bool, view: QWebEngineView):
        """
        PDF打印完成后的槽函数。
        """
        if success:
            print(f"成功保存 PDF: {file_path}")
        else:
            print(f"保存 PDF 失败: {file_path}")
        
        self._task_finished(view)
        
    def _task_finished(self, view: QWebEngineView):
        """
        当一个任务（无论成功与否）结束后，进行清理并启动下一个任务。
        """
        self.active_jobs -= 1
        print(f"一个任务已完成 (当前活动任务: {self.active_jobs})")

        # 清理视图资源
        view.deleteLater()
        self.active_views.remove(view)

        # 尝试启动下一个任务
        if self.tasks:
            self._start_next_task()
        elif self.active_jobs == 0:
            # 如果队列和活动任务都为空，则所有工作完成
            print("所有任务已完成。")
            QCoreApplication.instance().quit()


def convertHtmlToPdf(url_list):
    """
    将一个 URL 列表批量转换为 PDF 文件。
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    manager = ConversionManager(url_list)
    manager.start()

    sys.exit(app.exec())

def Main():
    pass
    # convertHtmlToPdf([
    #     ["https://blog.rainppr.dns-dynamic.net/whk/science/sequence/1/", "数列 1.pdf"],
    #     ["https://blog.rainppr.dns-dynamic.net/whk/science/sequence/2/", "数列 2.pdf"],
    #     ["https://blog.rainppr.dns-dynamic.net/whk/science/sequence/3/", "数列 3.pdf"],
    #     ["https://blog.rainppr.dns-dynamic.net/whk/science/sequence/4/", "数列 4.pdf"],
    # ])

if __name__ == "__main__":
    Main()
