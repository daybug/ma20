import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt
import base64
from datetime import datetime, timedelta
import time

import io
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import matplotlib
matplotlib.use('Agg')  # 非交互式后端，避免GUI问题

class EmailReporter:
    def __init__(self, smtp_server, smtp_port, username, password):
        """初始化邮件发送配置"""
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password

    def create_html_content(self, index_data):
        """生成HTML邮件内容，包含最近10条数据和图表"""
        html_content = """
        <html>
        <head><style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
            th {{ background-color: #f2f2f2; }}
            .alert {{ color: red; font-weight: bold; }}
            .normal {{ color: green; }}
            .chart-container {{ margin: 20px 0; text-align: center; }}
            img {{ max-width: 100%; height: auto; border: 1px solid #eee; }}
            .summary {{ background: #f9f9f9; padding: 15px; border-radius: 5px; margin: 10px 0; }}
        </style></head>
        <body>
        """
        html_content = html_content + f'<h2>📊 指数监控报告 - {datetime.now().strftime("%Y-%m-%d")}</h2>'
        # 添加汇总信息
        total_alerts = sum(1 for name, df in index_data.items()
                           if not df.empty and df.iloc[-1]['收盘'] < df.iloc[-1]['ma20'])
        html_content += f'<div class="summary">监控指数: {len(index_data)} 个 | 告警指数: {total_alerts} 个</div>'

        for name, df in index_data.items():
            if df.empty:
                continue

            # 最近10条数据表格
            recent_data = df.tail(10).copy()
            recent_data.index = recent_data.index.strftime('%Y-%m-%d')

            html_content += f"<h3>📈 {name} 监控详情</h3>"

            # 状态指示
            latest = recent_data.iloc[-1]
            status_class = "alert" if latest['收盘'] < latest['ma20'] else "normal"
            status_text = "⚠️ 低于MA20" if latest['收盘'] < latest['ma20'] else "✅ 高于MA20"

            html_content += f'''
            <div class="{status_class}">
                <strong>当前状态:</strong> {status_text} | 
                收盘价: {latest['收盘']:.2f} | 
                MA20: {latest['ma20']:.2f} |
                差值: {(latest['收盘'] - latest['ma20']):.2f}
            </div>
            '''

            # 数据表格
            html_content += recent_data[['收盘', 'ma20']].to_html(classes='data-table')

            # 图表占位符（将在后续替换为内嵌图片）
            html_content += f'''
            <div class="chart-container">
                <h4>{name} 走势图</h4>
                <img src="cid:{name}_chart" alt="{name}走势图">
            </div>
            <hr style="margin: 30px 0;">
            '''

        html_content += "</body></html>"

        return html_content

    def generate_chart_image(self, name, df):
        """生成指数图表并返回图片二进制数据"""
        plt.figure(figsize=(12, 6))
        plt.plot(df.index, df['收盘'], label='收盘价', linewidth=2, color='#2E86AB')
        plt.plot(df.index, df['ma20'], label='20日均线', linestyle='--', linewidth=2, color='#A23B72')

        # 标注跌破点
        below_ma = df[df['收盘'] < df['ma20']]
        if not below_ma.empty:
            plt.scatter(below_ma.index, below_ma['收盘'], color='red', s=60,
                        label='跌破MA20', alpha=0.7, edgecolors='black')

        plt.title(f'{name} 收盘价与20日均线走势', fontsize=14, fontweight='bold')
        plt.xlabel('日期', fontsize=12)
        plt.ylabel('点位', fontsize=12)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()

        # 保存图片到内存
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=120, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()

        return img_buffer.getvalue()

    def send_report(self, index_data, recipient, subject="指数监控报告"):
        """发送包含内嵌图表和数据的邮件"""
        # 创建邮件
        msg = MIMEMultipart()
        msg['From'] = self.username
        msg['To'] = recipient
        msg['Subject'] = subject+datetime.now().strftime("%Y-%m-%d")

        # 生成HTML内容
        html_content = self.create_html_content(index_data)

        # 创建带内嵌图片的HTML部分
        html_part = MIMEMultipart('related')
        html_part.attach(MIMEText(html_content, 'html'))

        # 为每个指数生成图表并内嵌到邮件中
        for name, df in index_data.items():
            if df.empty:
                continue

            # 生成图表图片
            chart_data = self.generate_chart_image(name, df)
            base64_data = base64.b64encode(chart_data).decode('utf-8')

            # 替换CID引用为Base64数据URL
            html_content = html_content.replace(
                f'src="cid:{name}_chart"',
                f'src="data:image/png;base64,{base64_data}"'
            )
            # 创建图片附件并设置Content-ID用于内嵌
            img = MIMEImage(chart_data)
            img.add_header('Content-ID', f'{name}_chart')
            img.add_header('Content-Disposition', 'inline', filename=f'{name}_chart.png')
            html_part.attach(img)

        msg.attach(html_part)

        # 同时附加原始图片作为附件（可选）
        # for name, df in index_data.items():
        #     if not df.empty:
        #         chart_data = self.generate_chart_image(name, df)
        #         attachment = MIMEImage(chart_data)
        #         attachment.add_header('Content-Disposition', 'attachment',
        #                               filename=f'{name}_chart_{datetime.now().strftime("%Y%m%d")}.png')
        #         msg.attach(attachment)

        # 发送邮件
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            print(f"✅ 邮件已发送至: {recipient}")
            return True
        except Exception as e:
            print(f"❌ 邮件发送失败: {str(e)}")
            return False


# 设置中文显示
plt.rcParams["font.family"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

class AKIndexDataCrawler:
    def __init__(self):
        """初始化AKShare指数数据爬虫"""
        # 指数代码映射表 (AKShare使用的指数代码)
        self.index_codes = {
            "中丐": "164906",
            "恒生医药ETF": "159892",
            "恒生科技指数ETF": "513180",
            "创业板华夏ETF": "159957",
            "上证50": "000016",
            "沪深300": "000300",
            "中证500": "000905",
            "中证1000": "000852"
        }
    
    def get_index_data(self, index_name, start_date=None, end_date=None, days=120):
        """
        获取指定指数的历史数据并计算MA20
        
        参数:
            index_name: 指数名称，如"上证50"
            start_date: 开始日期，格式"YYYY-MM-DD"
            end_date: 结束日期，格式"YYYY-MM-DD"
            days: 如果不指定start_date，默认获取最近days天的数据
        
        返回:
            DataFrame: 包含指数数据及MA20的DataFrame
        """
        if index_name not in self.index_codes:
            raise ValueError(f"不支持的指数名称: {index_name}，支持的指数有: {list(self.index_codes.keys())}")
        
        code = self.index_codes[index_name]
        print(f"正在获取{index_name}({code})的数据...")
        
        # 如果未指定日期范围，默认获取最近days天的数据
        if not start_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        try:
            # 使用AKShare获取指数历史数据
            df = ak.index_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date,
                end_date=end_date
            )
            
            if df.empty:
                print(f"未获取到{index_name}的数据，请检查日期范围是否正确")
                return None
            
            # 数据处理 - 不同版本可能返回不同的列名，统一处理
            if "收盘" not in df.columns and "收盘价" in df.columns:
                df.rename(columns={"收盘价": "收盘"}, inplace=True)
            if "日期" not in df.columns and "交易日期" in df.columns:
                df.rename(columns={"交易日期": "日期"}, inplace=True)
            
            df["日期"] = pd.to_datetime(df["日期"])
            df.set_index("日期", inplace=True)
            df = df.sort_index()
            
            # 计算MA20（20日移动平均线）
            df["ma20"] = df["收盘"].rolling(window=20, min_periods=1).mean()
            
            return df
            
        except Exception as e:
            print(f"获取{index_name}数据时出错: {str(e)}")
            return None
    
    def check_ma20_cross(self, index_name, df):
        """
        检查指数是否收盘价低于MA20，并发出告警
        
        参数:
            index_name: 指数名称
            df: 包含收盘和ma20数据的DataFrame
        """
        if df is None or df.empty:
            return
            
        # 获取最新的5条数据，检查是否有收盘价低于MA20的情况
        recent_data = df[["收盘", "ma20"]].tail(5)
        
        # 检查最新数据是否收盘价低于MA20
        latest_data = recent_data.iloc[-1]
        if not pd.isna(latest_data["ma20"]) and latest_data["收盘"] < latest_data["ma20"]:
            print("\n" + "="*60)
            print(f"⚠️  告警: {index_name} 最新收盘价低于20日均线 ⚠️")
            print(f"日期: {recent_data.index[-1].strftime('%Y-%m-%d')}")
            print(f"收盘价: {latest_data['收盘']:.2f}")
            print(f"20日均线: {latest_data['ma20']:.2f}")
            print(f"差值: {latest_data['收盘'] - latest_data['ma20']:.2f}")
            print("="*60 + "\n")
        
        # 检查是否有刚刚跌破的情况（前一天在均线上，今天在均线下）
        if len(recent_data) >= 2:
            prev_data = recent_data.iloc[-2]
            if (not pd.isna(prev_data["ma20"]) and not pd.isna(latest_data["ma20"]) and
                prev_data["收盘"] >= prev_data["ma20"] and 
                latest_data["收盘"] < latest_data["ma20"]):
                print("\n" + "="*60)
                print(f"⚠️  重要告警: {index_name} 刚刚跌破20日均线 ⚠️")
                print(f"前一交易日({recent_data.index[-2].strftime('%Y-%m-%d')}): "
                      f"收盘价 {prev_data['收盘']:.2f} > MA20 {prev_data['ma20']:.2f}")
                print(f"最新交易日({recent_data.index[-1].strftime('%Y-%m-%d')}): "
                      f"收盘价 {latest_data['收盘']:.2f} < MA20 {latest_data['ma20']:.2f}")
                print("="*60 + "\n")
    
    def get_multiple_index_data(self, index_names=None, days=120, check_alert=True):
        """
        批量获取多个指数的数据，并可选检查告警条件
        
        参数:
            index_names: 要获取的指数名称列表
            days: 获取最近天数的数据
            check_alert: 是否检查并发出告警
        
        返回:
            dict: 包含各指数数据的字典
        """
        if not index_names:
            index_names = list(self.index_codes.keys())
            
        index_data = {}
        for name in index_names:
            data = self.get_index_data(name, days=days)
            if data is not None:
                index_data[name] = data
                # 检查是否需要发出告警
                if check_alert:
                    self.check_ma20_cross(name, data)
            # 避免请求过于频繁
            time.sleep(1)
        
        return index_data
    
    def plot_index_data(self, index_data, indicators=["收盘", "ma20"]):
        """绘制指数数据图表，标注跌破均线的位置"""
        for name, df in index_data.items():
            plt.figure(figsize=(12, 6))
            
            # 绘制收盘价和MA20
            for indicator in indicators:
                if indicator in df.columns:
                    plt.plot(df.index, df[indicator], label=indicator)
            
            # 标注收盘价低于MA20的点
            below_ma = df[df["收盘"] < df["ma20"]]
            if not below_ma.empty:
                plt.scatter(below_ma.index, below_ma["收盘"], 
                           color='red', s=30, alpha=0.6, label="低于20日均线")
            
            plt.title(f"{name} 指数走势 (收盘价与20日均线)")
            plt.xlabel("日期")
            plt.ylabel("点位")
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.legend()
            plt.tight_layout()
            plt.show()

    def send_email_report(self, index_data, recipient, smtp_config=None):
        """
        发送指数监控报告邮件

        参数:
            index_data: 指数数据字典
            recipient: 收件人邮箱
            smtp_config: SMTP配置字典，包含server, port, username, password
        """
        if not smtp_config:
            smtp_config = {
                'server': 'smtp.example.com',
                'port': 587,
                'username': 'your_email@example.com',
                'password': 'your_password'
            }

        reporter = EmailReporter(
            smtp_config['server'],
            smtp_config['port'],
            smtp_config['username'],
            smtp_config['password']
        )

        reporter.send_report(index_data, recipient)

# 修改main函数
if __name__ == "__main__":
    # 初始化爬虫
    crawler = AKIndexDataCrawler()

    # 获取所有指数最近120天的数据
    index_data = crawler.get_multiple_index_data(days=120, check_alert=True)

    # 配置邮件发送
    smtp_config = {
        'server': 'smtp.163.com',
        'port': 25,
        'username': 'xxx@163.com',
        'password': 'your password'
    }

    # 发送邮件报告
    if index_data:
        crawler.send_email_report(
            index_data,
            recipient='xxx@xxx.cn',
            smtp_config=smtp_config
        )
    else:
        print("未获取到数据，无法发送邮件")
    
