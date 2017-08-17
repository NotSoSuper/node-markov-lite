import re

class MarkovLite:
	def __init__(self, cursor):
		self.cursor = cursor
		self.sql = "SELECT * FROM `markov` WHERE message LIKE %s OR message LIKE %s ORDER BY RAND() LIMIT 1"
		self.regex = re.compile(r'\s+')

	async def learn(self, message):
		content = self.regex.sub(' ', message.content.strip())
		await self.cursor.execute('INSERT INTO `markov` (`user`, `name`, `message`) VALUES (%s, %s, %s)', \
														 (message.author.id, message.author.name, content))

	def get_words(self, sentence:str):
		if re.match(r'^\s*$', sentence):
			return []
		return self.regex.split(sentence)

	def get_chain(self, words:list, depth:int=2):
		out = []
		for i in range(depth):
			try:
				out.append(words[len(words) - depth + i])
			except IndexError:
				break
		return out

	def match_chain(self, words:list, chain:list, depth:int=2):
		out = []
		for i in range(len(words)):
			word = words[i]
			if not chain or word == chain[0]:
				acceptable = True
				for i2 in range(len(chain)):
					if chain[i2] != words[i + i2]:
						acceptable = False
						break
				if acceptable:
					if len(chain) < depth:
						for i2 in range(i, min(i + depth, len(words))):
							out.append(words[i2])
					else:
						for i2 in range(1, len(chain)):
							out.append(chain[i2])
						try:
							out.append(words[i + len(chain)])
						except IndexError:
							pass
					break
		return out

	async def query(self, chain:str):
		sentence = " ".join(chain)
		if sentence.strip() == "":
			q = await self.cursor.execute('SELECT * FROM `markov` ORDER BY RAND() LIMIT 1')
			return await q.fetchone()
		q = await self.cursor.execute(self.sql, (f"%{sentence}%", f"%{sentence}%"))
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
			if ((len(chain) - len(last_chain)) <= 0) and len(chain) < depth:
				break
			elif len(last_chain) < depth:
				for i in range(len(last_chain), len(chain) - 1):
					out.append(chain[i])
			else:
				out.append(chain[len(chain) - 1])
		return " ".join(out)