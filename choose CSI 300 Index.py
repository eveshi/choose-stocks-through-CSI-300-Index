#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2017-09-14 23:40:10
# @Author  : Your Name (you@example.org)
# @Link    : http://example.org
# @Version : $Id$

import os
import numpy as np
import pandas as pd
import chardet
import requests
from bs4 import BeautifulSoup
import xlrd

#4个函数，一个导入股票名单，一个看财报说里面我们要的Roe，一个看股价（包括求每股净值），一个merge输出到表格

class caipaoPa(object):
	"""docstring for caipaoPa"""
	def __init__(self):
		self.obData = pd.read_excel('./300.xlsx')
		self.obData.columns = ['date','index code','index name','index name eng','constituent code',
		                       'constituent name','constituent name eng','exchange']

		self.compNums = self.obData.loc[:,['constituent code']].values
		self.compPla = self.obData.loc[:,['exchange']].values
		self.compName = self.obData.loc[:,['constituent name eng']].values
		self.caibaoIndex = pd.DataFrame(columns=['公司名称','公司代码','上市地点','RoE2012','2013','2014','2015','2016',
												 'RoE连续5年超过20%','现时股价','股价低点（市盈率10）',
												 '股价正常（市盈率20）','股价高点（市盈率30）','是否可以购买'])

	def RoE(self):
		#每个公司在财报说的链接
		compList = []

		i = 0
		for number in self.compNums:
			compStr = 'http://caibaoshuo.cn/companies/' + str(self.compNums[i][0]).zfill(6)
			compList.append(compStr)
			i += 1

		#计算每个公司RoE
		compRoe = pd.DataFrame([])

		r = 0
		for item in compList:
			#判断网页状态
			dataSt = requests.get(compList[r])
			#网页状态正常时
			if dataSt.status_code == requests.codes.ok:
				print('true')
				compData = pd.read_html(compList[r])

				#分解网页上的三个表格
				f1 = compData[1]
				f2 = compData[2]
				f3 = compData[3]

				#重命名索引，扔掉不要的列
				f1.columns = ['name','2012','2013','2014','2015','2016','0']
				f1.index = ['财务结构','负债占资产比率(%)','长期资金占不动产及设备比率(%)',
							'偿债能力','流动比率(%)','速动比率(%)',
							'营运能力','应收账款周转率(次/年)','应收账款周转天数(天)',
		            		'存货周转率(次/年)','存货周转天数(天)','固定资产周转率(次/年) ',
		            		'总资产周转率(次/年)','盈利能力','ROA=资产收益率(%)',
		            		'ROE=净资产收益率(%)','税前纯益占实收资本比率(%)','毛利率(%)',
		            		'营业利润率(%)','净利率(%)','基本每股收益(每股盈余EPS)',
		            		'现金流量','现金流量比率','现金流量充当比率','现金再投资比率']
				f1New = f1.dropna(axis=1, how='all')
				#提取RoE
				newCompRoe = f1New.loc[['ROE=净资产收益率(%)'],['2012','2013','2014','2015','2016']]
				roeAr = newCompRoe.values.reshape((1,5))
			
				#因为有的是string，有的是float，所以判断string格式，先把里面不能用的数据改成0.0
				if roeAr.dtype == object:
					roeAr[roeAr=='--'] = 0.0

				roeAr = roeAr.astype(float)
				newCompRoe = pd.DataFrame(roeAr)
				# newCompRoe = np.ndarray.tolist(newCompRoe)

			#网页状态异常时
			else:
				print('false')
				newCompRoe = pd.DataFrame({'0' : 0.0,
										   '1' : 0.0,
										   '2' : 0.0,
										   '3' : 0.0,
										   '4' : 0.0}, index=[0])
				print newCompRoe

			newCompRoe.index = [r]
			compRoe = compRoe.append(newCompRoe)
			r += 1

		#把RoE变成array
		# self.compRoeAr = np.array(compRoe)
		#储存RoE
		print compRoe
		roeData = pd.DataFrame(compRoe)
		roeData.to_csv('/Users/eveshi/Documents/007project/learnPython/caibaoshuo/roeData.csv')

		#判断RoE是否连续5年大于20%（也移动到最后一个整合函数）
		
	def price(self):
		#每个公司在雪球的链接
		compListXQ = []

		strCompPla = self.compPla.astype(str)

		plaList = []

		a = 0
		for item in strCompPla:
			if str(strCompPla[a][0]) == np.array('SHH'):
				plaList.append('SH')
			elif str(strCompPla[a][0]) == np.array('SHZ'):
				plaList.append('SZ')
			a += 1

		b = 0
		for number in self.compNums:
			compStr = 'https://xueqiu.com/S/' + plaList[b] + str(self.compNums[b][0]).zfill(6)
			compListXQ.append(compStr)
			b += 1

		#抓取页面中的每股净值和股价
		nps = []
		sp = []

		headers = {
		    'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'
		}

		c = 0
		for item in compListXQ:
			response = requests.get(compListXQ[c],headers = headers)

			# 抓取每股净值
			nps1 = BeautifulSoup(response.text,'lxml').find(title='最近报告期每股净资产，单位：人民币')
			nps2 = nps1.find('span').get_text()
			nps3 = float(nps2)
			nps.append(nps3)

			#抓取股价
			sp1 = BeautifulSoup(response.text,'lxml').find(attrs = {"class":"currentInfo"}).find('strong')
			if sp1 == None:
				# sp2 = BeautifulSoup(response.text,'lxml').find(attrs = {"class":"stock-closed"}).get_text()
				sp3 = 0.0
			else:
				sp2 = sp1['data-current']
				sp3 = float(sp2)
			sp.append(sp3)

			c += 1

		# #储存净值和股价
		npsData = pd.DataFrame(nps)
		npsData.to_csv('/Users/eveshi/Documents/007project/learnPython/caibaoshuo/npsData.csv')
		spData = pd.DataFrame(sp)
		spData.to_csv('/Users/eveshi/Documents/007project/learnPython/caibaoshuo/spData.csv')

		#计算合理股价范围(最后决定把这一块放在最后一部分，这样前面的数据可以先储存)

	def merge(self):
		#读取所有已储存数据
		readRoe = pd.read_csv('roeData.csv')
		readNps = pd.read_csv('npsData.csv')
		readSp = pd.read_csv('spData.csv')

		compRoe2012 = readRoe.iloc[:,[1]].values
		compRoe2013 = readRoe.iloc[:,[2]].values
		compRoe2014 = readRoe.iloc[:,[3]].values
		compRoe2015 = readRoe.iloc[:,[4]].values
		compRoe2016 = readRoe.iloc[:,[5]].values
		compRoe = readRoe.iloc[:,[1,2,3,4,5]].values

		nps = readNps.iloc[:,[1]].values
		sp = readSp.iloc[:,[1]].values
		print sp
		print nps

		#计算股价合理范围
		price10 = 10*compRoe2016*nps/100
		price20 = 20*compRoe2016*nps/100
		price30 = 30*compRoe2016*nps/100

		print price10

		#判断股价
		spBool = []
		i = 0
		for item in price20:
			if price20[i][0] > sp[i][0] and sp[i][0] != 0.0:
				spBool.append(['YES'])
			else:
				spBool.append(['--'])
			i += 1

		spBoolAr = np.array(spBool)
		spBoolAr.transpose
		print spBoolAr

		#判断RoE是否连续5年>20%
		roeBool = []

		i = 0
		for item in compRoe:
			if np.any(compRoe[i]<20) == True:
				roeBool.append(['--'])
			else:
				roeBool.append(['YES'])
			i += 1

		#储存判断结果
		boolData = np.array(roeBool)
		boolData.transpose
		print boolData

		buy = []
		i = 0
		for item in roeBool:
			if roeBool[i][0] == 'YES' and spBoolAr[i][0] == 'YES':
				buy.append(['Buy'])
			else:
				buy.append(['--'])
			i += 1

		caibaoIn = np.concatenate((self.compName, self.compNums, self.compPla,
								   compRoe2012, compRoe2013, compRoe2014, compRoe2015, compRoe2016,
								   roeBool, sp, price10, price20, price30, spBool, buy),
								   axis=1)
		self.caibaoIndex = pd.DataFrame(caibaoIn,
									columns=['constituent name','constituent code','exchange','RoE in 2012',
											 'RoE in 2013','RoE in 2014','RoE in 2015','RoE in 2016',
											 'RoE>20% in 5 years','price now','low price',
											 'regular price','high price','good price','buy or not'])
		print self.caibaoIndex
		self.caibaoIndex.to_csv('/Users/eveshi/Documents/007project/learnPython/caibaoshuo/caibaoIndex.csv', encoding='utf-8')



caipaoPa().RoE()
caipaoPa().price()
caipaoPa().merge()
