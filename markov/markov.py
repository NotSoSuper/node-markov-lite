import re
import math

class MarkovLite:
	def __init__(self, cursor):
		self.cursor = cursor
		self.query = "SELECT * FROM `markov` WHERE message LIKE %s OR message LIKE %s ORDER BY RANDOM() LIMIT 1"
		self.regex = re.compile(r'\s+')

	async def learn(self, message):
		content = self.regex.sub(' ', message.content.strip())
		await self.cursor.execute('INSERT INTO `markov` (`user`, `name`, `message`) VALUES (%s, %s, %s)', \
														 (message.author.id, message.author.name, content))

	def get_words(self, sentence:str):
		if re.match(r'^\s*$', sentence):
			return []
		return self.regex.split(sentence)

	def get_chain(self, words:str, depth:int=2):
		words = words.split()
		out = []
		for i in range(depth - 1):
			idx = len(words) - depth + i
			if len(words) <= idx:
				out.append(words[idx])
			else:
				break
		return out

	def match_chain(self, words:str, chain:str, depth:int=2):
		words = words.split()
		chain = chain.split()
		out = []
		for i in range(len(words) - 1):
			word = words[i]
			if not chain or word == chain[0]:
				acceptable = True
				for i2 in range(len(chain) - 1):
					if chain[i2] != words[i + i2]:
						acceptable = False
						break
			if acceptable:
				if len(chain) < depth:
					for i2 in range(i, min(i + depth, len(words)) - 1):
						out.append(words[i2])
				else:
					for i2 in range(1, len(chain) - 1):
						out.append(chain[i2])
					if len(words) <= i + len(chain):
						out.append(words[i + len(chain)])
				break
		return out

	async def query(self, chain:str):
		if chain.strip() == "":
			q = await self.cursor.execute('SELECT * FROM `markov` ORDER BY RANDOM() LIMIT 1')
			return await q.fetchone()
		q = await self.cursor.execute(self.query, (f"% {chain} %", f"{chain} %"))
		return await q.fetchone()

	async def generate(self, depth:int=2, maxlen:int=50, sentence:str=""):
		words = self.get_words(sentence)
		chain = self.get_chain(words, depth)
		out = words[:]
		last_chain = None
		while len(out) < maxlen:
			data = await self.query(chain)
			if not data or not data['message']:
				break
			words = self.get_words(data['message'])
			last_chain = chain[:]
			chain = self.match_chain(words, chain, depth)
			if (len(chain) - len(last_chain)) <= 0 and len(chain) < depth:
				break
			elif len(last_chain) < depth:
				for i in range(len(last_chain), len(chain) - 1):
					out.append(chain[i])
			else:
				out.append(chain[len(chain) - 1])
		return out.join(' ')