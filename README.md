# 📊 指数监控与邮件报告系统

一个基于 Python 的自动化指数数据监控工具，能够实时获取股票指数数据，计算技术指标，并通过邮件发送包含图表和分析报告。

## ✨ 功能特性

- **📈 多指数监控**：支持上证指数、深证成指、创业板指等主要A股指数
- **📊 技术分析**：自动计算20日均线(MA20)并检测突破信号
- **📧 智能报告**：生成包含数据表格和图表的HTML邮件报告
- **🔔 实时告警**：当指数跌破关键均线时发送预警通知
- **🖼️ 可视化展示**：内嵌走势图表，支持邮件客户端和网页端查看

## 🛠️ 技术栈

- **Python 3.7+**
- `akshare` - 金融数据接口
- `pandas` - 数据处理与分析
- `matplotlib` - 数据可视化
- `smtplib` - 邮件发送服务
- `email` - 邮件内容构建

## 📦 安装依赖

```bash
pip install akshare pandas matplotlib
```

## ⚙️ 配置说明

### 1. 邮箱服务配置

在代码中配置您的SMTP服务器信息：

```python
smtp_config = {
    'server': 'smtp.163.com',    # SMTP服务器地址
    'port': 25,                  # 端口号
    'username': 'your_email@163.com',  # 发件邮箱
    'password': 'your_password'        # 授权码/密码
}
```

### 2. 支持的指数列表

默认监控以下指数：
- `沪深300` (000300)
- `上证50` (000016)
- `科创50` (000688)
- `中概互联ETF` (164906)
- `恒生医药ETF` (159892)
- `恒生科技指数ETF` (513180)
- `创业板华夏ETF` (159957)
- `中证500` (000905)
- `中证1000` (000852)

也可根据需要自行添加，如：
- `上证指数` (000001)
- `深证成指` (399001)
- `创业板指` (399006)

## 🚀 使用方法

### 基本使用

```python
from ma20 import AKIndexDataCrawler

# 初始化爬虫
crawler = AKIndexDataCrawler()

# 获取单个指数数据
df = crawler.get_index_data('上证指数', days=180)

# 批量获取所有指数数据
index_data = crawler.get_multiple_index_data(days=180, check_alert=True)

# 发送邮件报告
crawler.send_email_report(index_data, 'recipient@example.com')
```

### 命令行运行

```bash
python ma20.py
```

程序将自动：
1. 获取所有监控指数的历史数据
2. 计算20日均线和技术指标
3. 检测突破信号并打印告警
4. 发送包含图表的邮件报告

## 📧 邮件报告内容

每封邮件包含：

### 📋 数据表格
- 最近10个交易日的收盘价和MA20值
- 当前状态指示（高于/低于均线）
- 价格差异统计

### 📊 走势图表
- 收盘价曲线（蓝色实线）
- 20日均线曲线（粉色虚线）
- 跌破均线的点位标注（红色圆点）

### ⚠️ 告警信息
- 实时监控状态变化
- 突破信号的即时通知

## 🎯 输出示例

### 控制台输出
```
⚠️  告警: 上证指数 最新收盘价低于20日均线 ⚠️
✅  深证成指 运行在20日均线上方
📧 邮件已成功发送至: user@example.com
```

### 邮件内容
![邮件示例](https://via.placeholder.com/800x600?text=邮件报告预览)

## 🔧 自定义配置

### 添加新的监控指数

```python
# 在 AKIndexDataCrawler.__init__() 中添加指数映射
self.index_codes = {
    '上证指数': '000001',
    '你的指数': '指数代码',
    # ... 更多指数
}
```

### 调整监控参数

```python
# 修改监控天数
index_data = crawler.get_multiple_index_data(days=120)  # 120天历史数据

# 禁用告警检查  
index_data = crawler.get_multiple_index_data(check_alert=False)
```

### 自定义邮件主题

```python
crawler.send_email_report(
    index_data, 
    recipient='user@example.com',
    subject='我的自定义监控报告'
)
```

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- [AKShare](https://github.com/akfamily/akshare) - 提供优质的金融数据接口

## ⚠️ 免责声明

本工具仅供技术学习和研究使用，不构成任何投资建议。金融市场有风险，投资需谨慎。使用者应自行承担因使用本工具而产生的所有责任和风险。

---

如有问题或建议，请通过 Issue 反馈或联系维护者。
