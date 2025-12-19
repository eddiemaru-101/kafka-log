로그
- 콘텐츠 재생(contents-start) - EventCategory: 2, EventType: 4
- 콘텐츠 일시정지(contents-pause) - EventCategory: 2, EventType: 6
- 콘텐츠 재시작(contents-start-resume) - EventCategory: 2, EventType: 7
- 콘텐츠 중지(contents-stop)- EventCategory: 2, EventType: 5

핵심 제약:

- 재생 없이 일시정지는 불가
- 일시정지 없이 재시작은 불가
- 중지(exit)는 언제든 가능하지만 보통 **재생 중 / 일시정지 중**에 발생




| 패턴 타입 | 의미 |
| --- | --- |
| 콘텐츠 재생 → stop | 즉시 이탈 |
| 콘텐츠 재생 → 콘텐츠 일시정지 → stop | 중단 이탈 |
| 콘텐츠 재생 → 콘텐츠 일시정지 → Resume → stop | 정상 시청 |
| 콘텐츠 재생 → 콘텐츠 일시정지 → Resume → 콘텐츠 일시정지 → stop | 잦은 끊김 |


시청시간 관련 로그 발생 조건
-콘텐츠 재생(contents-start)가 발생하면 4가지 패턴중 한가지로 발생한다.
-콘텐츠 재생(contents-start)가 발생하면 해당 패턴에 포함된 타입의 로그가 모두 발생되어 sink된다.
-설정값의 활성도등급 상,중,하 비율에 따라 콘텐츠 재생(contents-start) 로그 시간과 콘텐츠 중지(contents-stop)의 로그 시간의 간격이 달라져야한다.(시청시간으로 집계시 사용을 위해서)
-시간의 간격은 설정값의 활성도 등급별 평균 시청시간에 noise를 더해서 로그 내용 생성시 부여한다.
-콘텐츠 재생(contents-start), 콘텐츠 중지(contents-stop)의 로그 시간 간격은 활성도 등급별 평균시청시간에 따라 부여하고 콘텐츠 일시정지, 콘텐츠 재시작(contents-start-resume)의 로그 시간은 평균 시청시간 내에서 random으로 간격을 부여해서 로그를 발생시킨다. 
