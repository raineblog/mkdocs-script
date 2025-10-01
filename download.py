import sys
import os
from collections import deque

from PySide6.QtCore import QCoreApplication, QUrl, Slot, QMarginsF
from PySide6.QtGui import QPageLayout, QPageSize
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage, QWebEngineProfile
from PySide6.QtWebEngineWidgets import QWebEngineView

class SilentWebEnginePage(QWebEnginePage):
    """A custom QWebEnginePage that suppresses JavaScript console messages."""
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        pass

class ConversionManager:
    """
    在主线程中管理多个网页到PDF的转换任务。
    利用一个固定大小的工作池来重用QWebEngineView实例，以实现最佳缓存效果。
    """
    def __init__(self, url_list, max_concurrent_jobs: int = 8):
        self.tasks = deque(url_list)
        self.max_concurrent_jobs = max_concurrent_jobs
        
        # --- MODIFICATION 2: Setup a persistent profile for caching ---
        # 使用一个独立的、持久化的配置文件，而不是默认的
        self.profile = QWebEngineProfile("PersistentProfile")
        cache_dir = "web_cache"
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        self.profile.setCachePath(cache_dir)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
        self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
        print(f"浏览器缓存目录设置为: {os.path.abspath(cache_dir)}")

        # --- MODIFICATION 3: Create a reusable worker pool ---
        self.idle_workers = []
        self.active_workers = {}  # Maps a view (worker) to its current output_path

        for i in range(self.max_concurrent_jobs):
            view = QWebEngineView()
            # 为每个视图设置使用我们共享配置文件的页面
            page = SilentWebEnginePage(self.profile, view)
            view.setPage(page)
            view.settings().setAttribute(QWebEngineSettings.WebAttribute.PrintElementBackgrounds, True)
            
            # 信号只需连接一次，使用lambda传递view实例
            view.loadFinished.connect(lambda ok, v=view: self._on_load_finished(ok, v))
            page.pdfPrintingFinished.connect(lambda path, ok, v=view: self._on_pdf_printed(path, ok, v))
            
            self.idle_workers.append(view)

        # 定义页面布局和边距 (单位: 毫米)
        margins = QMarginsF(19, 25.5, 19, 25.5)
        self.page_layout = QPageLayout(
            QPageSize(QPageSize.PageSizeId.A4),
            QPageLayout.Orientation.Portrait,
            margins,
            QPageLayout.Unit.Millimeter,
        )
        print(f"任务管理器已初始化，共有 {len(self.tasks)} 个任务，工作池大小: {len(self.idle_workers)}")

    def start(self):
        """开始处理任务队列。"""
        self._assign_tasks_to_workers()

    def _assign_tasks_to_workers(self):
        """为所有空闲的worker分配新任务。"""
        while self.idle_workers and self.tasks:
            worker = self.idle_workers.pop(0)  # 从空闲池中取出一个worker
            url, output_path = self.tasks.popleft()
            
            self.active_workers[worker] = output_path  # 标记为活动并记录其任务
            
            print(f"分配任务: {url} -> {output_path} (剩余任务: {len(self.tasks)})")
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            worker.load(QUrl(url))

    # --- MODIFICATION 4: Signal handlers now manage the worker pool ---
    @Slot(bool, QWebEngineView)
    def _on_load_finished(self, success: bool, view: QWebEngineView):
        output_path = self.active_workers.get(view)
        if not output_path:
            return  # 如果worker不在活动列表中，则忽略

        if success:
            print(f"页面加载成功: {view.url().toString()}")
            view.page().printToPdf(output_path, self.page_layout)
        else:
            print(f"页面加载失败: {view.url().toString()}")
            self._task_finished(view) # 加载失败也需释放worker

    @Slot(str, bool, QWebEngineView)
    def _on_pdf_printed(self, file_path: str, success: bool, view: QWebEngineView):
        if success:
            print(f"成功保存 PDF: {file_path}")
        else:
            print(f"保存 PDF 失败: {file_path}")
        
        self._task_finished(view)
        
    def _task_finished(self, view: QWebEngineView):
        """一个任务完成，回收worker并尝试分配新任务。"""
        print(f"一个任务已完成 (活动任务: {len(self.active_workers) - 1})")
        
        # 从活动池中移除，并归还到空闲池
        if view in self.active_workers:
            del self.active_workers[view]
        self.idle_workers.append(view)

        # 立即检查是否有等待的任务需要处理
        self._assign_tasks_to_workers()

        # 如果所有任务都已分配且所有worker都已空闲，则工作完成
        if not self.tasks and not self.active_workers:
            print("所有任务已完成。")
            # 清理所有worker资源
            while self.idle_workers:
                worker = self.idle_workers.pop()
                worker.deleteLater()
            QCoreApplication.instance().quit()


def convertHtmlToPdf(url_list):
    """将一个 URL 列表批量转换为 PDF 文件。"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    manager = ConversionManager(url_list)
    manager.start()

    sys.exit(app.exec())

def Main():
    print("test download")
    convertHtmlToPdf([
        ["https://blog.rainppr.dns-dynamic.net/whk/science/sequence/1/", "数列 1.pdf"],
        ["https://blog.rainppr.dns-dynamic.net/whk/science/sequence/2/", "数列 2.pdf"],
        ["https://blog.rainppr.dns-dynamic.net/whk/science/sequence/3/", "数列 3.pdf"],
        ["https://blog.rainppr.dns-dynamic.net/whk/science/sequence/4/", "数列 4.pdf"],
    ])

if __name__ == "__main__":
    Main()
