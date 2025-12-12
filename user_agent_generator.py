import random

# 랜덤 버전 생성 유틸 함수
def v(*ranges):
    """
    브라우저 또는 엔진 버전용 랜덤 숫자 조합 생성.
    예:
        v((100,150), (0,10), (0,500)) → "143.3.421"
    매개변수 형태:
        (start, end) 튜플을 여러 개 넣으면 각 자리의 범위가 된다.
    """
    return ".".join(str(random.randint(r[0], r[1])) for r in ranges)

def random_ios_build():
    """
    iOS 빌드 번호 realistic 생성.
    예: "15E148", "16F203"
    - 앞자리: 14~18 무작위 (iOS Major)
    - 중간 알파벳: E/F/G 중 랜덤
    - 마지막 숫자: 100~300 랜덤
    """
    major = random.randint(14, 18)
    letter = random.choice(["E", "F", "G"])
    num = random.randint(100, 300)
    return f"{major}{letter}{num}"

#  PC User-Agent (Chrome, Whale)
def random_pc_user_agent():
    chrome_version = v((120, 145), (0, 3), (0, 5000), (0, 200))
    whale_version = f"{random.randint(3,5)}.{random.randint(10,40)}.{random.randint(100,400)}.{random.randint(1,99)}"

    candidates = [
        # Chrome on Windows
        f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        f"AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36",

        # Whale browser (Chromium 기반)
        f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        f"AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Whale/{whale_version} Safari/537.36"
    ]

    return random.choice(candidates)

# Android User-Agent (Chrome, SamsungBrowser)
def random_android_user_agent():
    chrome_version = v((120, 145), (0, 5), (0, 9999), (0, 999))
    samsung_version = f"{random.randint(15, 30)}.{random.randint(0,3)}"

    android_version = random.choice([8, 9, 10, 11, 12, 13, 14])
    model_code = random.choice(["K", "SM-G990", "SM-G998", "A52", "A53"])

    candidates = [
        # Chrome on Android
        f"Mozilla/5.0 (Linux; Android {android_version}; {model_code}) "
        f"AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36",

        # Samsung Browser
        f"Mozilla/5.0 (Linux; Android {android_version}; {model_code}) "
        f"AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/{samsung_version} "
        f"Chrome/{chrome_version} Safari/537.36"
    ]

    return random.choice(candidates)

# iOS User-Agent (Safari, Chrome/CriOS)
def random_ios_user_agent():
    ios_major = random.randint(16, 18)
    ios_minor = random.randint(0, 7)
    ios_patch = random.randint(0, 5)
    ios_version = f"{ios_major}_{ios_minor}_{ios_patch}"

    safari_engine = "605.1.15"  # iOS 계열 기본 엔진은 크게 변하지 않음
    build = random_ios_build()

    crios_version = v((120, 145), (0,10), (0,9999), (0,999))

    candidates = [
        # Safari on iPhone
        f"Mozilla/5.0 (iPhone; CPU iPhone OS {ios_version} like Mac OS X) "
        f"AppleWebKit/{safari_engine} (KHTML, like Gecko) "
        f"Version/{ios_major}.{ios_minor} Mobile/{build} Safari/604.1",

        # Chrome on iPhone (CriOS)
        f"Mozilla/5.0 (iPhone; CPU iPhone OS {ios_version} like Mac OS X) "
        f"AppleWebKit/{safari_engine} (KHTML, like Gecko) "
        f"CriOS/{crios_version} Mobile/{build} Safari/604.1"
    ]

    return random.choice(candidates)

# 전체 통합 Random User-Agent
def random_user_agent():
    generators = [
        random_pc_user_agent,
        random_android_user_agent,
        random_ios_user_agent
    ]
    return random.choice(generators)()

if __name__ == "__main__":
    for _ in range(10):
        print(random_user_agent())
