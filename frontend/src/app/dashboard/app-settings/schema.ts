import { z } from "zod";

export const appSettingsSchema = z.object({
  allowUserRegistration: z.boolean({
    message: "Please specify whether user registration is allowed",
  }),
  allowMultipleAdmins: z.boolean({
    message: "Please specify whether multiple admins are allowed",
  }),
});

export type AppSettingsFormData = z.infer<typeof appSettingsSchema>;
