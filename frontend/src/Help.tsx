import { badge, c, card, muted, pageTitle, sectionTitle } from './ui'

function Step({ n, title, children }: { n: number; title: string; children: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', gap: 12, marginBottom: 14 }}>
      <div
        style={{
          flexShrink: 0,
          width: 26,
          height: 26,
          borderRadius: 999,
          background: c.accentSoft,
          color: c.accent,
          fontWeight: 700,
          fontSize: 14,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {n}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontWeight: 600, marginBottom: 2 }}>{title}</div>
        <div style={{ ...muted, fontSize: 13.5 }}>{children}</div>
      </div>
    </div>
  )
}

export default function Help() {
  return (
    <section>
      <h2 style={pageTitle}>도움말 · 사용 설명서</h2>

      <div style={card}>
        <div style={sectionTitle}>이 앱은?</div>
        <p style={{ ...muted, margin: '6px 0 0' }}>
          소설을 회차별로 넣으면 <b>일관된 화풍·캐릭터</b>로 만화 컷을 만들어 주는 프로그램입니다.
          모든 데이터는 <b>내 PC에만</b> 저장되고, 그림·글 생성은 <b>내 API 키</b>로 직접 호출됩니다
          (생성 단계에는 인터넷이 필요해요).
        </p>
      </div>

      <div style={card}>
        <div style={sectionTitle}>1. 처음 한 번 — API 키 넣기</div>
        <p style={{ ...muted, margin: '6px 0 10px' }}>
          상단 <b>설정</b>에서 키를 입력합니다. 둘 중 하나만 있으면 시작할 수 있어요.
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{ padding: 10, border: `1px solid ${c.border}`, borderRadius: 8 }}>
            <span style={badge('success')}>무료</span>{' '}
            <b>Gemini 키</b> — <code>aistudio.google.com/apikey</code> 에서 무료 발급. 설정에서
            <b> “무료 버전 사용”</b>을 켜면 이 키로 동작합니다. 품질은 낮지만 비용이 없어요.
          </div>
          <div style={{ padding: 10, border: `1px solid ${c.border}`, borderRadius: 8 }}>
            <span style={badge('accent')}>유료</span>{' '}
            <b>Anthropic(Claude) 키</b> — <code>console.anthropic.com</code> 에서 발급. 품질이 가장
            좋고, 사용한 만큼 <b>본인에게 과금</b>됩니다.
          </div>
        </div>
        <p style={{ ...muted, fontSize: 12.5, marginTop: 10, marginBottom: 0 }}>
          키는 <b>Windows 자격증명 관리자</b>에만 저장되고 화면엔 가려서 표시됩니다. 저장 시 실제
          호출로 유효성을 검사해요.
        </p>
      </div>

      <div style={card}>
        <div style={sectionTitle}>2. 만화 만드는 순서</div>
        <div style={{ marginTop: 10 }}>
          <Step n={1} title="프로젝트 만들기">
            대시보드에서 새 프로젝트를 만들고 <b>화풍</b>(예: “로맨스 판타지풍, 부드러운 채색”)을
            적습니다. 이 화풍이 모든 회차의 기본값으로 고정돼요.
          </Step>
          <Step n={2} title="회차 본문 넣기">
            <b>회차</b> 탭에서 소설 본문을 붙여넣고 저장합니다.
          </Step>
          <Step n={3} title="인물 추출 · 캐릭터 뱅크">
            “인물 추출”로 등장인물을 뽑아 저장합니다. <b>캐릭터</b> 탭에서 인물별 외형·참조 이미지를
            등록하면 그림 일관성이 좋아져요.
          </Step>
          <Step n={4} title="콘티(컷) 생성">
            회차의 “콘티 생성”으로 장면을 컷으로 나눕니다.
          </Step>
          <Step n={5} title="컷 이미지 만들기">
            각 컷에서 <b>이미지 자동생성</b>(무료 Pollinations) 하거나, <b>프롬프트 복사</b> →
            Gemini 웹에서 참조 이미지로 그린 뒤 <b>이미지 업로드</b> 할 수 있어요.
          </Step>
          <Step n={6} title="대사 넣기">
            말풍선을 <b>드래그</b>해 위치를 정하고 “대사 합성”을 누릅니다. 폰트·말풍선 스타일은
            설정 탭에서 바꿔요.
          </Step>
          <Step n={7} title="모아 보기 · 내보내기">
            “만화 보기”로 세로 스크롤 감상, 상단에서 <b>PNG / PDF / ZIP</b>으로 내보냅니다.
          </Step>
        </div>
      </div>

      <div style={card}>
        <div style={sectionTitle}>3. 비용과 저장 위치</div>
        <ul style={{ ...muted, fontSize: 13.5, margin: '8px 0 0', paddingLeft: 18, lineHeight: 1.7 }}>
          <li>
            <b>비용</b>: 무료 모드(Gemini·Pollinations)는 <b>$0</b>. Claude 사용 시 프로젝트 <b>설정
            탭 → 사용량·예상 비용</b>에서 대략적인 지출을 확인할 수 있어요.
          </li>
          <li>
            <b>내 데이터</b>: <code>%LOCALAPPDATA%\convertN2C</code> (프로젝트·이미지·DB). 설정 →
            스토리지에서 “폴더 열기”로 열 수 있어요.
          </li>
          <li>
            <b>내보낸 만화</b>: <code>문서\convertN2C 내보내기</code> 폴더에 저장됩니다.
          </li>
        </ul>
      </div>

      <div style={card}>
        <div style={sectionTitle}>4. 문제 해결</div>
        <ul style={{ ...muted, fontSize: 13.5, margin: '8px 0 0', paddingLeft: 18, lineHeight: 1.7 }}>
          <li>
            <b>“인증 실패 / 키를 확인하세요”</b> → 설정에서 키를 다시 입력하세요(만료·오타).
          </li>
          <li>
            <b>“요청 한도 초과”</b> → 잠시(1분+) 후 재시도. 무료 Gemini는 분당 한도가 있어요.
          </li>
          <li>
            <b>“인터넷 연결 실패”</b> → 생성 단계는 온라인이 필요합니다. 연결을 확인하세요.
          </li>
          <li>
            <b>같은 인물이 매번 다르게 나와요</b> → 무료 그림(Pollinations)은 얼굴 일관성이 약합니다.
            캐릭터 참조 이미지로 외형을 등록하거나, Gemini 웹에서 만들어 업로드하세요.
          </li>
        </ul>
      </div>
    </section>
  )
}
