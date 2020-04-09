from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
from sys import platform
from multiprocessing import Process, Queue
import traceback
import logging
import numpy as np
import random

unpackedExtensionPath = "../src"


if platform == "linux" or platform == "linux2":
	# linux
	chromeDriverPath = '/home/schasins/Downloads/chromedriver'
	extensionkey = "clelgfmpjhkenbpdddjihmokjgooedpl"
elif platform == "darwin":
	# OS X
	chromeDriverPath = '/Users/schasins/Downloads/chromedriver'
	extensionkey = "bcnlebcnondcgcmmkcnmepgnamoekjnn"

def newDriver(profile):
	chrome_options = Options()
	chrome_options.add_argument("--load-extension=" + unpackedExtensionPath)
	chrome_options.add_argument("user-data-dir=profiles/" + profile)

	driver = webdriver.Chrome(chromeDriverPath, chrome_options=chrome_options)

	driver.get("chrome-extension://" + extensionkey + "/pages/mainpanel.html")
	return driver

def runScrapingProgram(profile, progId, optionsStr):

	driver = newDriver(profile)
	runScrapingProgramHelper(driver, progId, optionsStr)

	return driver
	
def runScrapingProgramHelper(driver, progId, optionsStr):
	driver.execute_script("window.helenaMainpanel.UIObject.loadSavedProgram(" + str(progId) + ");")

	runCurrentProgramJS = """
	function repeatUntilReadyToRun(){
		console.log("repeatUntilReadyToRun");
		if (!window.helenaMainpanel.UIObject.currentHelenaProgram){
			setTimeout(repeatUntilReadyToRun, 1000);
		}
		else{
			window.helenaMainpanel.UIObject.currentHelenaProgram.runProgram(""" + optionsStr + """);
		}
	}
	repeatUntilReadyToRun();
	"""
	driver.execute_script(runCurrentProgramJS)
	

def blockingRepeatUntilNonFalseAnswer(lam):
	ans = lam()
	while (not ans):
		time.sleep(1)
		ans = lam()
	return ans

def getDatasetIdForDriver(driver):
	getDatasetId = lambda : driver.execute_script("console.log('datasetsScraped', datasetsScraped); if (datasetsScraped.length > 0) {console.log('realAnswer', datasetsScraped[0]); return datasetsScraped[0];} else { return false;}")
	return blockingRepeatUntilNonFalseAnswer(getDatasetId)

def getWhetherDone(driver):
	getHowManyDone = lambda: driver.execute_script("console.log('scrapingRunsCompleted', scrapingRunsCompleted); if (scrapingRunsCompleted === 0) {return false;} else {return scrapingRunsCompleted}")
	return blockingRepeatUntilNonFalseAnswer(getHowManyDone)

class RunProgramProcess(Process):

        def __init__(self, allDatasets, i, profile, programId, optionStr, numTriesSoFar=0):
                super(RunProgramProcess,self).__init__()

                self.allDatasets = allDatasets
                self.profile = profile
                self.programId = programId
                self.optionStr = optionStr
                self.numTriesSoFar = numTriesSoFar
		self.driver = newDriver(self.profile)
                # below is bad, but I'm going to do it anyway for time being
                #self.driver = runScrapingProgram(self.profile, self.programId, self.optionStr)

        def run(self):
                self.runInternals()

        def runInternals(self):
                try:
			print self.optionStr
			runScrapingProgramHelper(self.driver, self.programId, self.optionStr)
                        datasetId = getDatasetIdForDriver(self.driver)
                        print self.programId, datasetId
                        self.allDatasets.put(datasetId)
                        done = getWhetherDone(self.driver)
                        print self.programId, done
                        self.driver.close()
                        self.driver.quit()
                except Exception as e:
                        # assume we can just recover by trying again
                        if (self.numTriesSoFar < 3):
                                self.numTriesSoFar += 1
                                self.runInternals()
                        else:
                                logging.error(traceback.format_exc())

        def terminate(self):
		try:
		    if (self.driver):
			    self.driver.close()
			    self.driver.quit()
		except: # catch *all* exceptions
		    print "tried to close driver but no luck. probably already closed"
                super(RunProgramProcess, self).terminate()
                

"""
def entityScopeVsNoEntityScopeFirstRunExperiment(programIdsLs):
	for programId in programIdsLs:
                allDatasets = Queue()
		p1 = RunProgramProcess(allDatasets,"1",programId,'{}')
		p2 = Process(target=runProgramThread, args=(allDatasets,"2",programId,'{ignoreEntityScope: true}'))
		d1 = p1.start()
		d2 = p2.start()
		p1.join()
		p2.join()
		print "------"

	print allDatasets
	for datasetId in allDatasets:
		print "kaofang.cs.berkeley.edu:8080/downloaddetailed/" + str(datasetId)

"""

def joinProcesses(procs, timeoutInSeconds):
        pnum = len(procs)
        bool_list = [True]*pnum
        start = time.time()
        while time.time() - start <= timeoutInSeconds:
                for i in range(pnum):
                        bool_list[i] = procs[i].is_alive()
                if np.any(bool_list):
                        time.sleep(1)
                else:
                        print "time to finish: ", time.time() - start
                        return True
        else:
                print "timed out, killing all processes", time.time() - start
                for p in procs:
                        p.terminate()
                        p.join()
                return False
   

def oneConfigRun(programId, i, j, allDatasetsAllIterations, simulatedErrorLocs):
	noErrorsRunComplete = False
	allDatasets = None
	while (not noErrorsRunComplete):
		allDatasets = Queue()
		errorLoc = simulatedErrorLocs[programId][i]
		simulateErrorIndexesStr = str(errorLoc)
		print simulateErrorIndexesStr

		p2 = RunProgramProcess(allDatasets,2, "2",programId,'{nameAddition: "+escope+loc'+str(i)+'+run'+str(j)+'", simulateError:'+ simulateErrorIndexesStr + '}') # our recovery strategy
		p3 = RunProgramProcess(allDatasets,3, "3",programId,'{nameAddition: "+ideal+loc'+str(i)+'+run'+str(j)+'"}') # the perfect ideal recovery strategy, won't encounter simulated error
		p4 = RunProgramProcess(allDatasets,4, "4",programId,'{nameAddition: "+ideal+loc'+str(i)+'+run'+str(j)+'", ignoreEntityScope: true}') # an alternative perfect ideal recovery strategy, won't encounter simulated error, but also won't use entityScope
		p1 = RunProgramProcess(allDatasets,1, "1",programId,'{nameAddition: "+naive+loc'+str(i)+'+run'+str(j)+'", ignoreEntityScope: true, simulateError:'+ simulateErrorIndexesStr + '}') # naive recovery strategy
		
		procs = [p2,p3,p4,p1]
		for p in procs:
			time.sleep(3) # don't overload; also, wait for thing to load
			p.start()
		
		# below will be true if all complete within the time limit, else false
		noErrorsRunComplete = joinProcesses(procs, 4000)

	print "------"

	f = open("recoveryDatasetUrls.txt", "a")
	for i in range(4):
		newDatasetId = allDatasets.get()
		allDatasetsAllIterations.append(newDatasetId)
		f.write("kaofang.cs.berkeley.edu:8080/downloaddetailedmultipass/" + str(newDatasetId) + "\n")
	f.close()

	for datasetId in allDatasetsAllIterations:
		print "kaofang.cs.berkeley.edu:8080/downloaddetailedmultipass/" + str(datasetId)

	print "------"

def recoveryExperiment(programIdsLs, simulatedErrorLocs, rounds):
        allDatasetsAllIterations = []
	for programId in programIdsLs:
		for j in range(rounds): # do three runs
			for i in range(len(simulatedErrorLocs[programId])):
                                 oneConfigRun(programId, i, j, allDatasetsAllIterations, simulatedErrorLocs)

def shortRecoveryTest(programIdsLs, simulatedErrorLocs):
        allDatasetsAllIterations = []
        for programId in programIdsLs:
                oneConfigRun(programId, 0, 0, allDatasetsAllIterations, simulatedErrorLocs)


def main():
	programIds = [\
                      #145, \
                      #152 \
                      #138, \
                      #128, \
                      #143, \
                      #151, \
                      #149, \
		      #154,
		      #155
		      #158,
		      #155,
		      159
        ]
	simulatedErrorLocs = {
		128: [[27], [54], [81]], # community foundations
                #143: [[1,525], [2,350], [3,175]], # old twitter
		155: [[2,100],[3,200],[4,300]], # new twitter
                138: [[10], [20], [30]], # craigslist
                #149: [[1, 1903], [1, 3805], [7, 1005]], # old yelp reviews
		154: [[4,225], [8,150], [12,75]], # new yelp reviews
                #145: [[10], [20], [30]], # yelp restaurant features
                145: [[10]], # yelp restaurant features the correction run
                158: [[10,20],[20,4],[30,7]], # yelp menu items
                159: [[10,20],[20,4],[30,7]], # yelp menu items (the mac version)
                #152: [[13],[25],[37]] # zimride listings
		152: [[8]] # zimride correction run
	}
	recoveryExperiment(programIds, simulatedErrorLocs, 3)
        #shortRecoveryTest(programIds, simulatedErrorLocs)

main()
