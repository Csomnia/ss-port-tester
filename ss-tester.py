import time, socks, socket, json, psutil, subprocess, requests
from multiprocessing.dummy import Pool as ThreadPool

class ss_test(object):
    urls = ['http://www.google.com', 'http://www.amazon.com',
            'http://www.ebay.com', 'http://www.alibaba.com',
            'http://www.reddit.com']
    record = dict()
    temp_name = "temp.json"
    def __init__(self, conf_name):
        with open(conf_name, 'r') as f:
            self.conf = json.load(f)
        self.set_socks()

    def set_socks(self):
        # set default socks
        socks.set_default_proxy(socks.SOCKS5,
                                self.conf['local_address'],
                                self.conf['local_port'])
        socket.socket = socks.socksocket

    def kill_ss(self):
        #if ss already running, kill it
        for proc in psutil.process_iter():
            if proc.name() == "sslocal":
                print("will kill sslocal already in %s" % proc.pid)
                try:
                    proc.kill()
                except:
                    print("neet to be root.")

    def ss_change(self, port):
        # generate conf for port.
        self.conf['server_port'] = port
        with open(self.temp_name, 'w') as f:
            json.dump(self.conf, f)

        # kill ss
        self.kill_ss()
        
        #call shell to change ss.
        ss_path = "/usr/local/bin/sslocal"
        temp_path = "/home/changrunqing/shadow-select/" + self.temp_name
        cmd = "nohup %s -c %s > /dev/null 2>&1 &" % (ss_path, temp_path)
        #print(cmd)
        excu = subprocess.Popen(cmd, shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        excu.communicate()
        
        # check process create?.
        while True:
            time.sleep(0.3)
            print("check.....sslocal in process?..")
            for proc in psutil.process_iter():
                if proc.name() == "sslocal":
                    print("switch to port: "+ str(port))
                    return;
                
    def port_test(self, port):
        #start spec port testing.
        sub_record = []
        #this shuould using map to reduce time usage.
        pool = ThreadPool(len(self.urls))
        results = pool.map(self.url_test, self.urls)
        return sum(results)
        # for url in self.urls:
        #     sub_record.append(self.url_test(url))
        #     self.record[port] = sum(sub_record) 


    def tester(self, port_list, times):
        for port in port_list:
            map_list = [port for i in range(times)]
            self.ss_change(port)
            pool = ThreadPool(times)
            result = pool.map(self.port_test, map_list)
            self.record[port] = sum(result)
        print(self.record)
        min_port = min(self.record.items(), key=lambda x: x[1])[0]
        print("best port is: %s" % min_port)
        self.ss_change(min_port)
        print("successful change to port: %s" % min_port)
        # for port in port_list:
        #     self.port_test(port)
        # print(self.record)
        

    def url_test(self, url):
        #test single url.
        try :
            nf = requests.get(url)
            page = nf.content
            elapsed = nf.elapsed.total_seconds()
            nf.close()
        except :
            print("connection failed.")
            time.sleep(0.8)
            return self.url_test(url)
        print ("url: "+url+" time "+ str(elapsed))
        time.sleep(0.1)
        return elapsed
        

if __name__ == "__main__":
    test = ss_test('data.json')
    #first arg is port , second is times.
    test.tester([443, 22, 8080], 2)
