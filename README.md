# SystemCheck

- 시스템 고장 예방, 탐지를 위해 자체 개발한 감시 환경
    - SystemCheckAgent.sh: Bash Shell Script로 개발 되어 라이브러리 종속성을 최소화하고, AgentToServer 방식으로 보안성을 높였습니다.
    - SystemChecker.py: SystemCheckAgent로 부터 수집된 데이터를 취합하고, Noti를 발송 합니다.
    
- 구성도

![System_Status_Check drawio (2)](https://user-images.githubusercontent.com/86950682/220089998-6788fda9-df72-413b-84b4-c512a8c779b9.png)
