# -*- coding:utf-8 -*-
"""
@Author:ddz
@Date:2025/3/7 11:10
@Project:dealSina
"""
import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import time
import os
import re

# Target URL for the Weibo topic about 南京理工大学
BASE_URL = "https://m.weibo.cn/search?containerid=100103type%3D1%26q%3D%23%E5%8D%97%E4%BA%AC%E7%90%86%E5%B7%A5%E5%A4%A7%E5%AD%A6%23"

# API endpoint for getting JSON data
API_URL = "https://m.weibo.cn/api/container/getIndex"

# Headers to mimic a browser request
HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1",
    "Accept": "application/json, text/plain, */*",
    "Referer": BASE_URL,
    "X-Requested-With": "XMLHttpRequest"
}


class WeiboScraper:
    def __init__(self):
        self.all_data = []
    
    def get_weibo_data(self, page=1):
        """获取微博数据的JSON"""
        params = {
            'containerid': '100103type=1&q=#南京理工大学#',
            'page_type': 'searchall',
            'page': page
        }
        try:
            response = requests.get(API_URL, headers=HEADERS, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"请求失败，状态码: {response.status_code}")
                return None
        except Exception as e:
            print(f"获取数据时出错: {e}")
            return None
    
    def parse_weibo_data(self, json_data):
        """解析微博JSON数据"""
        if not json_data or 'data' not in json_data or 'cards' not in json_data['data']:
            return []
        
        weibo_list = []
        for card in json_data['data']['cards']:
            if card.get('card_type') == 9:  # 微博卡片类型
                mblog = card.get('mblog')
                if mblog:
                    # 提取用户信息
                    user = mblog.get('user', {})
                    username = user.get('screen_name', '')
                    member_type = '会员' if user.get('verified', False) else '普通用户'
                    
                    # 提取微博内容
                    content = re.sub('<[^<]+?>', '', mblog.get('text', ''))  # 移除HTML标签
                    created_at = mblog.get('created_at', '')
                    reposts_count = mblog.get('reposts_count', 0)
                    comments_count = mblog.get('comments_count', 0)
                    attitudes_count = mblog.get('attitudes_count', 0)  # 点赞数
                    
                    # 提取图片URL
                    pics = []
                    if 'pics' in mblog:
                        for pic in mblog['pics']:
                            pics.append(pic.get('url', ''))
                    
                    # 构建数据字典
                    weibo_item = {
                        '用户名': username,
                        '会员类型': member_type,
                        '粉丝正文内容': content,
                        '发布时间': created_at,
                        '转发': reposts_count,
                        '评论': comments_count,
                        '点赞': attitudes_count,
                        '图片': pics
                    }
                    weibo_list.append(weibo_item)
        
        return weibo_list
    
    def scrape_weibo_topic(self, max_pages=10):
        """爬取微博话题的多页数据"""
        for page in range(1, max_pages + 1):
            print(f"正在爬取第{page}页...")
            json_data = self.get_weibo_data(page)
            if json_data:
                page_data = self.parse_weibo_data(json_data)
                if page_data:
                    self.all_data.extend(page_data)
                    print(f"第{page}页爬取成功，获取{len(page_data)}条微博")
                else:
                    print(f"第{page}页没有数据")
                    break
            else:
                print(f"获取第{page}页数据失败")
                break
            time.sleep(2)  # 避免请求过于频繁
    
    def save_to_json(self, filename='weibo_data.json'):
        """将数据保存为JSON文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.all_data, f, ensure_ascii=False, indent=4)
        print(f"数据已保存到{filename}")
    
    def save_to_excel(self, filename='weibo_data.xlsx'):
        """将数据保存为Excel文件"""
        df = pd.DataFrame(self.all_data)
        # 处理图片列表为字符串
        if '图片' in df.columns:
            df['图片'] = df['图片'].apply(lambda x: '\n'.join(x) if x else '')
        df.to_excel(filename, index=False)
        print(f"数据已保存到{filename}")


if __name__ == "__main__":
    scraper = WeiboScraper()
    try:
        # 爬取微博数据
        scraper.scrape_weibo_topic(max_pages=5)  # 默认爬取5页
        
        # 保存数据
        if scraper.all_data:
            # 保存为JSON格式
            scraper.save_to_json()
            
            # 保存为Excel
            scraper.save_to_excel()
            
            print(f"共爬取{len(scraper.all_data)}条微博数据")
        else:
            print("未获取到任何数据")
    except Exception as e:
        print(f"程序执行出错: {e}")


