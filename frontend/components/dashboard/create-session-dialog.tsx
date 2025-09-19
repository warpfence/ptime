'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { CreateSessionRequest } from '@/types/session';

interface CreateSessionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreateSession?: (data: CreateSessionRequest) => Promise<void>;
}

export function CreateSessionDialog({
  open,
  onOpenChange,
  onCreateSession,
}: CreateSessionDialogProps) {
  const [isLoading, setIsLoading] = useState(false);

  const form = useForm<CreateSessionRequest>({
    defaultValues: {
      title: '',
      description: '',
      max_participants: undefined,
    },
  });

  const onSubmit = async (data: CreateSessionRequest) => {
    try {
      setIsLoading(true);

      // max_participants가 빈 문자열이면 undefined로 변경
      const payload = {
        ...data,
        max_participants: data.max_participants || undefined,
      };

      if (onCreateSession) {
        await onCreateSession(payload);
      }

      // 폼 리셋 및 다이얼로그 닫기
      form.reset();
      onOpenChange(false);
    } catch (error) {
      console.error('세션 생성 오류:', error);
      // 에러 처리는 상위 컴포넌트에서 담당
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    form.reset();
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>새 세션 만들기</DialogTitle>
          <DialogDescription>
            새로운 프레젠테이션 세션을 생성합니다. 참여자들이 QR 코드나 세션 코드로 접속할 수 있습니다.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="title"
              rules={{
                required: '세션 제목을 입력해주세요',
                minLength: {
                  value: 2,
                  message: '제목은 최소 2자 이상이어야 합니다'
                },
                maxLength: {
                  value: 100,
                  message: '제목은 최대 100자까지 입력 가능합니다'
                }
              }}
              render={({ field }) => (
                <FormItem>
                  <FormLabel>세션 제목 *</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="예: 2024 분기별 성과 발표"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="description"
              rules={{
                maxLength: {
                  value: 500,
                  message: '설명은 최대 500자까지 입력 가능합니다'
                }
              }}
              render={({ field }) => (
                <FormItem>
                  <FormLabel>세션 설명</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="세션에 대한 간단한 설명을 입력하세요 (선택사항)"
                      className="resize-none"
                      rows={3}
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    참여자들에게 표시될 세션 설명입니다.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="max_participants"
              rules={{
                min: {
                  value: 1,
                  message: '최소 1명 이상이어야 합니다'
                },
                max: {
                  value: 1000,
                  message: '최대 1000명까지 설정 가능합니다'
                }
              }}
              render={({ field }) => (
                <FormItem>
                  <FormLabel>최대 참여자 수</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      placeholder="제한 없음"
                      min={1}
                      max={1000}
                      {...field}
                      onChange={(e) => {
                        const value = e.target.value;
                        field.onChange(value === '' ? undefined : parseInt(value, 10));
                      }}
                      value={field.value || ''}
                    />
                  </FormControl>
                  <FormDescription>
                    비워두면 참여자 수에 제한이 없습니다.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <DialogFooter className="gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={handleCancel}
                disabled={isLoading}
              >
                취소
              </Button>
              <Button type="submit" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                    생성 중...
                  </>
                ) : (
                  '세션 생성'
                )}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}