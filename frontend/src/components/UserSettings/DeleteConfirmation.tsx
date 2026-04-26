import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"

import { UsersService } from "@/client"
import { ConfirmDialog } from "@/components/Common/ConfirmDialog"
import { Button } from "@/components/ui/button"
import useAuth from "@/hooks/useAuth"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

const DeleteConfirmation = () => {
  const [open, setOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const { logout } = useAuth()

  const mutation = useMutation({
    mutationFn: () => UsersService.deleteUserMe(),
    onSuccess: () => {
      showSuccessToast("Hisobingiz muvaffaqiyatli o'chirildi")
      setOpen(false)
      logout()
    },
    onError: handleError(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["currentUser"] })
    },
  })

  return (
    <>
      <Button
        variant="destructive"
        className="mt-3"
        onClick={() => setOpen(true)}
      >
        Hisobni o'chirish
      </Button>
      <ConfirmDialog
        open={open}
        onOpenChange={setOpen}
        title="Tasdiqlash kerak"
        description={
          <>
            Hisobingizdagi barcha ma'lumotlar{" "}
            <strong>butunlay o'chiriladi.</strong> Ishonchingiz komil bo'lsa,
            davom etish uchun <strong>"O'chirish"</strong> tugmasini bosing. Bu
            amalni qaytarib bo'lmaydi.
          </>
        }
        confirmText="O'chirish"
        destructive
        loading={mutation.isPending}
        onConfirm={() => mutation.mutate()}
      />
    </>
  )
}

export default DeleteConfirmation
