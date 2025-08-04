import { useResetPassword } from "@/api/hooks/authentication/use-reset-password";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { LoaderWrapper } from "@/components/ui/loader-wrapper";
import { images } from "@/constants/images";
import { paths } from "@/paths";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { Link } from "react-router";
import { toast } from "sonner";
import { z } from "zod";

const resetPasswordSchema = z.object({
  email: z.email("Invalid email address").min(1, "Email is required"),
});

type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>;

export const ResetPassword = () => {
  const resetPassword = useResetPassword();
  const form = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: {
      email: "",
    },
    disabled: resetPassword.isPending,
  });

  const onSubmit = async (data: ResetPasswordFormData) => {
    resetPassword.mutate(data, {
      onSuccess: () => {
        toast.success("Password reset email sent!", {
          description:
            "Check your inbox for instructions to reset your password.",
        });
        form.reset();
      },
      onError: (error) => {
        toast.error("Failed to send reset email", {
          description: error.message || "An unexpected error occurred.",
        });
      },
    });
  };

  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-gray-50 p-4">
      <Card className="w-full max-w-md rounded-md shadow-none">
        <CardHeader className="text-center">
          <div className="flex flex-col items-center space-y-3">
            <img
              src={images.candlestick}
              alt="AutoTrader Logo"
              className="h-16 w-16"
            />
            <div className="space-y-1">
              <CardTitle className="text-2xl font-semibold">
                Reset your password
              </CardTitle>
              <CardDescription className="text-sm text-gray-500">
                Enter the email address associated with your account
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email</FormLabel>
                    <FormControl>
                      <Input
                        type="email"
                        placeholder="Enter your email address"
                        autoComplete="email"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <Button
                type="submit"
                className="w-full"
                disabled={resetPassword.isPending}
              >
                <LoaderWrapper isLoading={resetPassword.isPending}>
                  Send reset email
                </LoaderWrapper>
              </Button>

              <Button
                asChild
                variant="ghost"
                type="button"
                className="-mt-3 w-full"
                disabled={resetPassword.isPending}
              >
                <Link to={paths.authentication.LOGIN}>Back to login</Link>
              </Button>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
};
