import { api } from "@/api/config";
import { useMutation } from "@tanstack/react-query";

interface NewWebhookSecretResponse {
  secret: string;
}

const fetchNewWebhookSecret = async () => {
  const response = await api.get<NewWebhookSecretResponse>(
    "users/me/settings/new-webhook-secret",
  );
  return response.json();
};

export const useNewWebhookSecret = () => {
  return useMutation({
    mutationFn: fetchNewWebhookSecret,
  });
};
