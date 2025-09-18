export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-center font-mono text-sm lg:flex">
        <div className="text-center">
          <h1 className="text-4xl font-bold mb-4">EngageNow</h1>
          <p className="text-xl mb-8">실시간 청중 참여 플랫폼</p>
          <div className="flex gap-4 justify-center">
            <button className="bg-primary text-primary-foreground px-6 py-3 rounded-lg hover:bg-primary/90">
              발표자 대시보드
            </button>
            <button className="border border-border px-6 py-3 rounded-lg hover:bg-accent">
              세션 참여하기
            </button>
          </div>
        </div>
      </div>
    </main>
  )
}