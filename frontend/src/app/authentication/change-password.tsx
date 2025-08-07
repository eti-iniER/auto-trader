import { useChangePassword } from "@/api/hooks/authentication/use-change-password";
import { useValidatePasswordResetToken } from "@/api/hooks/authentication/use-validate-password-reset-token";
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
import { motion, AnimatePresence } from "motion/react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useSearchParams } from "react-router";
import { toast } from "sonner";
import { z } from "zod";

const changePasswordSchema = z
  .object({
    newPassword: z
      .string()
      .min(8, "Password must be at least 8 characters long")
      .regex(
        /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
        "Password must contain at least one uppercase letter, one lowercase letter, and one number",
      ),
    confirmPassword: z.string(),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: "Passwords don't match",
    path: ["confirmPassword"],
  });

type ChangePasswordFormData = z.infer<typeof changePasswordSchema>;

export const ChangePassword = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get("token");
  const [isSuccess, setIsSuccess] = useState(false);

  const validateToken = useValidatePasswordResetToken(token || "", !!token);
  const changePassword = useChangePassword();

  const form = useForm<ChangePasswordFormData>({
    resolver: zodResolver(changePasswordSchema),
    defaultValues: {
      newPassword: "",
      confirmPassword: "",
    },
    disabled: changePassword.isPending,
  });

  useEffect(() => {
    if (!token) {
      toast.error("Invalid reset link", {
        description: "The password reset link is missing or invalid.",
      });
      navigate(paths.authentication.LOGIN);
    }
  }, [token, navigate]);

  const onSubmit = async (data: ChangePasswordFormData) => {
    changePassword.mutate(
      { newPassword: data.newPassword },
      {
        onSuccess: () => {
          setIsSuccess(true);
          toast.success("Password changed successfully!", {
            description: "You can now log in with your new password.",
          });
        },
        onError: (error) => {
          toast.error("Failed to change password", {
            description: error.message || "An unexpected error occurred.",
          });
        },
      },
    );
  };

  // Show loading while validating token
  if (validateToken.isLoading || !token) {
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
                  Validating reset link
                </CardTitle>
                <CardDescription className="text-sm text-gray-500">
                  Please wait while we verify your password reset link...
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="flex justify-center">
            <LoaderWrapper isLoading={true}>
              <div className="h-8 w-8" />
            </LoaderWrapper>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Show error if token validation failed
  if (validateToken.isError) {
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
                  Invalid reset link
                </CardTitle>
                <CardDescription className="text-sm text-gray-500">
                  This password reset link is invalid or has expired.
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Button asChild variant="outline" className="w-full">
                <Link to={paths.authentication.RESET_PASSWORD}>
                  Request new reset link
                </Link>
              </Button>
              <Button asChild variant="ghost" className="w-full">
                <Link to={paths.authentication.LOGIN}>Back to login</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

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
                {isSuccess ? "Password changed" : "Change your password"}
              </CardTitle>
              <CardDescription className="text-sm text-gray-500">
                {isSuccess
                  ? "Your password has been successfully changed"
                  : "Please enter your new password"}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <AnimatePresence mode="wait">
            {!isSuccess ? (
              <motion.div
                key="form"
                initial={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3, ease: "easeInOut" }}
              >
                <Form {...form}>
                  <form
                    onSubmit={form.handleSubmit(onSubmit)}
                    className="space-y-4"
                  >
                    <FormField
                      control={form.control}
                      name="newPassword"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>New password</FormLabel>
                          <FormControl>
                            <Input
                              type="password"
                              placeholder="Enter your new password"
                              autoComplete="new-password"
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="confirmPassword"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Confirm new password</FormLabel>
                          <FormControl>
                            <Input
                              type="password"
                              placeholder="Confirm your new password"
                              autoComplete="new-password"
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
                      disabled={changePassword.isPending}
                    >
                      <LoaderWrapper isLoading={changePassword.isPending}>
                        Change password
                      </LoaderWrapper>
                    </Button>

                    <Button
                      asChild
                      variant="ghost"
                      type="button"
                      className="-mt-3 w-full"
                      disabled={changePassword.isPending}
                    >
                      <Link to={paths.authentication.LOGIN}>Back to login</Link>
                    </Button>
                  </form>
                </Form>
              </motion.div>
            ) : (
              <motion.div
                key="success"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, ease: "easeInOut" }}
                className="space-y-4"
              >
                <Button asChild className="w-full">
                  <Link to={paths.authentication.LOGIN}>Continue to login</Link>
                </Button>
              </motion.div>
            )}
          </AnimatePresence>
        </CardContent>
      </Card>
    </div>
  );
};
