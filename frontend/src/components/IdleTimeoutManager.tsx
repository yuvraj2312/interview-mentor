import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { useIdleTimeout } from '@/hooks/useIdleTimeout'

export function IdleTimeoutManager() {
  const { secondsUntilLogout, stayActive } = useIdleTimeout()
  const open = secondsUntilLogout !== null

  return (
    <Dialog open={open} onOpenChange={(next) => !next && stayActive()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>You'll be logged out due to inactivity</DialogTitle>
          <DialogDescription>
            You'll be logged out in {secondsUntilLogout ?? 0} second{secondsUntilLogout === 1 ? '' : 's'} unless you
            stay active.
          </DialogDescription>
        </DialogHeader>
        <Button onClick={stayActive} className="w-fit">
          Stay signed in
        </Button>
      </DialogContent>
    </Dialog>
  )
}
