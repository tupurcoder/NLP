from subprocess import PIPE
import sys, subprocess
from collections import defaultdict
import time

v = defaultdict(float)
av = defaultdict(float)
T=5



def process(args):
  "Create a 'server' to send commands to."
  return subprocess.Popen(args, stdin=PIPE, stdout=PIPE)

def call(process, stdin):
  "Send command to a server and get stdout."
  output = process.stdin.write(stdin + "\n\n")
  line = ""
  while 1: 
    l = process.stdout.readline()
    if not l.strip(): break
    line += l
  return line

gold_server = process(
  ["python", "tagger_history_generator.py",  "GOLD"])
enum_server = process(
  ["python", "tagger_history_generator.py",  "ENUM"])
decoder_server = process(
  ["python", "tagger_decoder.py", "HISTORY"])

def getHistory(train_file):
  ftrain=open(train_file)
  trainlines = ftrain.readlines()
  
  sentence=""

  start_time=time.time()

  for t in xrange(T):
  	print (("\tIteration: %d")%(t+1))
	for line in trainlines:
		if line != "\n":
			sentence=sentence+line
		else:
			gold_history = call(gold_server, sentence.strip())
			enum_histories = call(enum_server, sentence.strip())
			ComputeFeatures(enum_histories, sentence, gold_history,t)
			sentence=""
			
  print (("\nExecution time: %f")%((time.time()-start_time)/60))

      
def ComputeFeatures(enum_histories, sentence, gold_history,t):
	weight=defaultdict(float)
	hist=""
	history_list = enum_histories.split("\n")
	word_list = sentence.split("\n")

	for item in history_list:
		elements = item.strip().split()
		if len(elements)==3:
			tempstring = word_list[int(elements[0])-1]
			tempstring=tempstring.strip().split()
			#print type(tempstring), tempstring, tempstring[0]

			if len(tempstring[0])==1:
				
				hist=hist+item+" "+str(v[(tempstring[0][-1:], elements[2])] + v[(tempstring[0], elements[2])] + v[(elements[1], elements[2])])+"\n"
			elif len(tempstring[0])==2:
				
				weight=v[(tempstring[0][-2:], elements[2])] + v[(tempstring[0][-1:], elements[2])] + v[(tempstring[0], elements[2])] + v[(elements[1], elements[2])]
				hist=hist+item+" "+str(weight)+"\n"
			else:
				
				weight = v[(tempstring[0][-1:], elements[2])] + v[(tempstring[0][-2:], elements[2])] + v[(tempstring[0][-3:], elements[2])] + v[(tempstring[0], elements[2])] + v[(elements[1], elements[2])]
				hist=hist+item+" "+str(weight)+"\n"
	
	decoder_history = call(decoder_server, hist.strip())

	f_gold = defaultdict(float)
	f_decoder = defaultdict(float)

	if decoder_history != gold_history:
		decoder_list = decoder_history.strip().split("\n")
		gold_list = gold_history.strip().split("\n")
		words = sentence.split("\n")
		#print len(gold_list), len(decoder_list), len(words), words
		for i in xrange(len(gold_list)):
			gold_list_elements = gold_list[i].strip().split()
			decoder_list_elements = decoder_list[i].strip().split()
			word_list = words[i].strip().split()
			#print word_list[0], len(word_list[0])

			f_gold[(word_list[0], gold_list_elements[2])] += 1
			f_decoder[(word_list[0], decoder_list_elements[2])] += 1
			f_decoder[(word_list[0], gold_list_elements[2])] += 0
			f_gold[(word_list[0], decoder_list_elements[2])] += 0

			f_gold[(gold_list_elements[1], gold_list_elements[2])] += 1
			f_decoder[(decoder_list_elements[1], decoder_list_elements[2])] += 1
			f_decoder[(gold_list_elements[1], gold_list_elements[2])] += 0
			f_gold[(decoder_list_elements[1], decoder_list_elements[2])] += 0


			if len(word_list[0])==1:
				f_gold[(word_list[0][-1:], gold_list_elements[2])] += 1
				f_decoder[(word_list[0][-1:], decoder_list_elements[2])] += 1
				f_decoder[(word_list[0][-1:], gold_list_elements[2])] += 0
				f_gold[(word_list[0][-1:], decoder_list_elements[2])] += 0

			elif len(word_list[0])==2:
				f_gold[(word_list[0][-1:], gold_list_elements[2])] += 1
				f_decoder[(word_list[0][-1:], decoder_list_elements[2])] += 1
				f_decoder[(word_list[0][-1:], gold_list_elements[2])] += 0
				f_gold[(word_list[0][-1:], decoder_list_elements[2])] += 0

				f_gold[(word_list[0][-2:], gold_list_elements[2])] += 1
				f_decoder[(word_list[0][-2:], decoder_list_elements[2])] += 1
				f_decoder[(word_list[0][-2:], gold_list_elements[2])] += 0
				f_gold[(word_list[0][-2:], decoder_list_elements[2])] += 0

			else:
				f_gold[(word_list[0][-1:], gold_list_elements[2])] += 1
				f_decoder[(word_list[0][-1:], decoder_list_elements[2])] += 1
				f_decoder[(word_list[0][-1:], gold_list_elements[2])] += 0
				f_gold[(word_list[0][-1:], decoder_list_elements[2])] += 0

				f_gold[(word_list[0][-2:], gold_list_elements[2])] += 1
				f_decoder[(word_list[0][-2:], decoder_list_elements[2])] += 1
				f_decoder[(word_list[0][-2:], gold_list_elements[2])] += 0
				f_gold[(word_list[0][-2:], decoder_list_elements[2])] += 0

				f_gold[(word_list[0][-3:], gold_list_elements[2])] += 1
				f_decoder[(word_list[0][-3:], decoder_list_elements[2])] += 1
				f_decoder[(word_list[0][-3:], gold_list_elements[2])] += 0
				f_gold[(word_list[0][-3:], decoder_list_elements[2])] += 0

		
		for key in f_gold.iterkeys():
			v[key]+=f_gold[key]-f_decoder[key]
			av[key]+=((t+1)*(f_gold[key]-f_decoder[key]))
			#print key, v[key]
	
	
if __name__ == '__main__':
	getHistory("tag_train.dat")
	fp1 = open("tag_train.dat")
	N=0
	trainlines = fp1.readlines()
	for line in trainlines:
		if line == "\n":
			N+=1
	fp1.close()
	fp = open("output/suffix_tagger.model", "w")
	for key in v.iterkeys():
		v[key]-=(av[key]/(T*N))
		if v[key]:
			fp.write(("%s:%s %f\n") %(key[0], key[1], v[key]))
	fp.close()




