System Check Agent 사용 방법

- mode 는 점검 결과의 출력을 콘솔 혹은, 파일로 정할 수 있습니다. 
콘솔과 파일을 제외한 모든 입력은 콘솔로 대체 됩니다.
  mode="file | console"
console mode로 사용 시 시스템에서 즉시 상태 점검이 가능 합니다. 실행 시 출력은 아래와 같습니다.
![console_example](https://user-images.githubusercontent.com/86950682/220094476-5ee3266e-3e6c-4864-8dc6-e47c3bde3736.PNG)


- disk_status 는 findmnt 명령을 통해 파일 시스템이 rw 상태가 아닐 경우를 체크 합니다.
  0: 정상 / 1: 비정상

- module_name은 로그스테시가 파싱 규칙을 적용할 때 사용되는 key 로 쓰입니다.
  module_name="system-check"

- false_fs 는 파일시스템 사용량, 아이노드 사용량, 디스크 상태 확인 시 제외할 파일 시스템을 정의 합니다.
  false_fs="/dev\|/run\|/sys\|/boot"






