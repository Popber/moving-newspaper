# 움직이는 신문 — Netlify + Render + Cloudinary

이 프로젝트는 **신문 전체가 움직이는 GIF 하나**로 생성되도록 구성되어 있습니다.

## 전체 흐름

1. Netlify 프론트에서 카메라 촬영
2. 3초 카운트다운 후 약 1.2초 영상 기록
3. 영상을 Render 백엔드 `/generate`로 전송
4. Render가 FFmpeg로 8프레임 추출
5. Pillow로 각 프레임을 해리포터풍 신문 전체에 합성
6. 서버에서 신문 전체 Animated GIF 생성
7. GIF를 Cloudinary에 업로드
8. 프론트에서 완성 GIF와 QR 표시

---

# 1. Render 배포

GitHub에 이 프로젝트 폴더를 올리는 것을 권장합니다.

Render에서:

1. **New + → Web Service**
2. GitHub 저장소 연결
3. Runtime은 Docker
4. Root Directory: `backend`
5. Dockerfile은 자동 인식
6. 환경변수 확인:
   - `CLOUDINARY_CLOUD_NAME=fhbtcmuv`
   - `CLOUDINARY_UPLOAD_PRESET=moving_newspaper`
7. Deploy

배포가 끝나면 예를 들어:

`https://moving-newspaper-api.onrender.com`

같은 URL이 생성됩니다.

브라우저에서:

`https://YOUR-RENDER-URL/health`

를 열어 `{"ok":true}`가 나오면 정상입니다.

> Render 무료 인스턴스는 한동안 사용하지 않으면 sleep 상태가 될 수 있어 첫 요청이 느릴 수 있습니다.
> 행사 전에는 반드시 서버를 미리 깨워두세요.

---

# 2. Netlify 프론트 설정

`frontend/config.js`를 열고:

```js
BACKEND_URL: "https://YOUR-RENDER-SERVICE.onrender.com"
```

부분에 실제 Render 주소를 넣습니다.

예:

```js
BACKEND_URL: "https://moving-newspaper-api.onrender.com"
```

그 다음 **frontend 폴더 안의 파일들**을 Netlify에 배포합니다.

Netlify 루트에는 다음 두 파일이 바로 보여야 합니다.

- `index.html`
- `config.js`

---

# 3. Cloudinary

이미 설정된 값:

- Cloud name: `fhbtcmuv`
- Unsigned upload preset: `moving_newspaper`

백엔드는 완성 GIF를 Cloudinary에 올리고 공개 URL을 반환합니다.

---

# 4. 행사 운영

1. Netlify 주소 접속
2. 카메라 켜기
3. 참가자 이름 입력
4. 촬영
5. `전체 신문 GIF 만들기`
6. 서버 처리
7. 완성 GIF 표시
8. QR 스캔 / GIF 저장
9. 다음 참가자 → 다시 촬영

---

# 디자인

- 오래된 황갈색 종이 질감
- 고전 신문 헤더 `THE YOUTH PROPHET`
- 포스터에서 가져온 `즐거움만수두룩! / 수리산 마법학교` 제목 이미지를 신문 내부에 삽입
- 본문은 영문 신문 기사 스타일
- 중앙 영역에 참가자 영상 프레임 삽입
- 최종 결과 전체가 하나의 Animated GIF

---

# 성능

브라우저가 아니라 Render 서버에서 GIF를 만드므로 모바일 GIF Worker 오류를 피할 수 있습니다.

현재 기본값:
- 촬영 약 1.2초
- 8프레임
- 최종 GIF 700×1000
- 프레임 간격 150ms
- 128색 팔레트

행사 속도가 중요하면 백엔드의 `W, H`를 `560, 800` 정도로 줄이면 더 빨라집니다.
