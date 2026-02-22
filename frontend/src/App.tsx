import { useState } from 'react'
import { Button } from '@/components/ui/button'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <h1 className="text-3xl font-bold">Wheelhouse</h1>
        <p className="text-muted-foreground">Options tracking dashboard</p>
        <Button onClick={() => setCount((c) => c + 1)}>
          Count is {count}
        </Button>
      </div>
    </div>
  )
}

export default App
