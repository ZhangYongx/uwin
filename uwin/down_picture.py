# -*- coding: utf -*-

import requests
from contextlib import closing


def download_image_imporve():
	# 伪造 headers 信息
	headers = {
		'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 \
		              (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36'
	}
	url = "https://assets-cdn.github.com/images/modules/about/about-header-2016.jpg"
	# response = requests.get(url, headers=headers, stream=True)
	# 执行完毕后，自动关闭流
	with closing(requests.get(url, headers=headers, stream=True)) as response:
		# 打开文件
		with open('demo1.jpg', 'wb') as fd:
			# 每128 写入一次
			for chunk in response.iter_content(128):
				fd.write(chunk)


download_image_imporve()