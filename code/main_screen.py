from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout
from PyQt5.Qt import Qt
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QPieSlice, QLegend, QBarSet, QBarSeries, QPercentBarSeries, \
    QBarCategoryAxis
from PyQt5.QtGui import QPainter, QPen, QColor
from utils import get_from_file


class BarChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        series = QBarSeries()
        data = get_from_file('data.txt', '')
        for title, val in [['audio-only', float(data['Audio-only WER']) / max(int(data['Audio-only samples']), 1) + 100],
                           ['video-only', float(data['Video-only WER']) / max(int(data['Video-only samples']), 1) + 100],
                           ['audio-video', float(data['Audio-video WER']) / max(int(data['Audio-video samples']), 1) + 100]]:
            set = QBarSet(title)
            set.append(val)
            set.setBrush(QColor('#4F4464'))
            pen = QPen(QColor('#292929'), self.width() * 0.1)
            set.setPen(pen)
            series.append(set)
        series.setBarWidth(1)
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle('Models WER')
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setBackgroundBrush(QColor('#292929'))
        chart.setTitleBrush(QColor('#FFFFFF'))
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        chart.legend().setMarkerShape(QLegend.MarkerShapeCircle)
        chart.legend().setLabelBrush(QColor('#FFFFFF'))
        chart.legend().setShowToolTips(True)
        chart.layout().setContentsMargins(0, 0, 0, 0)
        self.chart_view = QChartView(chart, self)
        self.chart_view.setRenderHint(QPainter.HighQualityAntialiasing)


    def resizeEvent(self, e):
        self.chart_view.setFixedSize(self.size())
        for set in self.chart_view.chart().series()[0].barSets():
            pen = QPen(QColor('#292929'), self.width() * 0.15)
            set.setPen(pen)


class PieChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        series = QPieSeries()
        data = get_from_file('data.txt', '')
        for title, val, color in [['audio-only', max(int(data['Audio-only used']), 1), '#6200EE'], ['video-only', max(int(data['Video-only used']), 1), '#BC9FE6'],
                                  ['audio-video', max(int(data['Audio-video used']), 1), '#9152EA']]:
            slice = series.append(title, val)
            slice.setBrush(QColor(color))
            slice.setPen(QColor('transparent'))
        chart = QChart()
        chart.addSeries(series)
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setTitle('Models usage')
        chart.setBackgroundBrush(QColor('#292929'))
        chart.setTitleBrush(QColor('#FFFFFF'))
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        chart.legend().setMarkerShape(QLegend.MarkerShapeCircle)
        chart.legend().setLabelBrush(QColor('#FFFFFF'))
        chart.legend().setShowToolTips(True)
        chart.layout().setContentsMargins(0, 0, 0, 0)
        self.chart_view = QChartView(chart, self)
        self.chart_view.setRenderHint(QPainter.HighQualityAntialiasing)

    def resizeEvent(self, e):
        self.chart_view.setFixedSize(self.size())


class MainWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            'background-color: #1B1B1B;'
        )
        self.pie_chart = PieChartWidget(parent=self)
        self.bar_chart = BarChartWidget(parent=self)

    def resizeEvent(self, e):
        self.pie_chart.setGeometry(int(self.width() * 0.0984375), int(self.height() * 0.224609375), int(self.width() * 0.3390625), int(self.height() * 0.55078125))
        self.bar_chart.setGeometry(int(self.width() * 0.5640625), int(self.height() * 0.263671875), int(self.width() * 0.34375), int(self.height() * 0.490234375))
