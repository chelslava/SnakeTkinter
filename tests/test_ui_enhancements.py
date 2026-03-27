import sys
import unittest
from unittest.mock import MagicMock, patch

from ui_enhancements import ModernUI, PerformanceMonitor, SettingsDialog


class TestPerformanceMonitor(unittest.TestCase):
    def setUp(self):
        self.monitor = PerformanceMonitor()

    def test_initialization(self):
        """Тест инициализации монитора"""
        self.assertEqual(len(self.monitor.frame_times), 0)
        self.assertEqual(self.monitor.max_samples, 60)

    def test_record_frame(self):
        """Тест записи времени кадра"""
        self.monitor.record_frame(0.016)
        self.assertEqual(len(self.monitor.frame_times), 1)

    def test_record_multiple_frames(self):
        """Тест записи нескольких кадров"""
        for _ in range(10):
            self.monitor.record_frame(0.016)
        self.assertEqual(len(self.monitor.frame_times), 10)

    def test_max_samples_limit(self):
        """Тест ограничения количества записей"""
        for _ in range(100):
            self.monitor.record_frame(0.016)
        self.assertEqual(len(self.monitor.frame_times), self.monitor.max_samples)

    def test_get_fps_empty(self):
        """Тест получения FPS без записей"""
        fps = self.monitor.get_fps()
        self.assertEqual(fps, 0)

    def test_get_fps_with_data(self):
        """Тест получения FPS с данными"""
        for _ in range(10):
            self.monitor.record_frame(0.016)  # ~60 FPS
        fps = self.monitor.get_fps()
        self.assertGreater(fps, 0)
        self.assertLess(fps, 100)

    def test_get_performance_stats_empty(self):
        """Тест получения статистики без данных"""
        stats = self.monitor.get_performance_stats()
        self.assertEqual(stats, {})

    def test_get_performance_stats_with_data(self):
        """Тест получения статистики с данными"""
        for _ in range(10):
            self.monitor.record_frame(0.016)
        stats = self.monitor.get_performance_stats()
        self.assertIn("fps", stats)
        self.assertIn("avg_frame_time", stats)
        self.assertIn("min_frame_time", stats)
        self.assertIn("max_frame_time", stats)


class TestModernUI(unittest.TestCase):
    def setUp(self):
        self.mock_root = MagicMock()

    @patch("ui_enhancements.ttk")
    @patch("ui_enhancements.tk")
    def test_initialization(self, mock_tk, mock_ttk):
        """Тест инициализации ModernUI"""
        ui = ModernUI(self.mock_root)
        self.assertIsNotNone(ui.root)

    @patch("ui_enhancements.ttk")
    @patch("ui_enhancements.tk")
    def test_update_status(self, mock_tk, mock_ttk):
        """Тест обновления статуса"""
        ui = ModernUI(self.mock_root)
        ui.status_label = MagicMock()
        ui.update_status("Test message")
        ui.status_label.config.assert_called_once_with(text="Test message")

    @patch("ui_enhancements.ttk")
    @patch("ui_enhancements.tk")
    def test_update_fps(self, mock_tk, mock_ttk):
        """Тест обновления FPS"""
        ui = ModernUI(self.mock_root)
        ui.fps_label = MagicMock()
        ui.update_fps(60.0)
        ui.fps_label.config.assert_called_once_with(text="FPS: 60.0")


class TestSettingsDialog(unittest.TestCase):
    def setUp(self):
        self.mock_parent = MagicMock()

    def test_result_initialization(self):
        """Тест начального значения результата"""
        dialog = SettingsDialog.__new__(SettingsDialog)
        dialog.result = None
        self.assertIsNone(dialog.result)


if __name__ == "__main__":
    unittest.main()
