import { type FormEvent, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { AuthCard, Field, inputClass } from "../components/common/AuthCard";
import { getErrorMessage } from "../services/api";
import { loginAccount } from "../services/auth";
import { useAuthStore } from "../store/authStore";

export function LoginPage() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);
  const accessToken = useAuthStore((state) => state.accessToken);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  if (accessToken) {
    return <Navigate to="/dashboard" replace />;
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setPending(true);
    setError(null);
    try {
      const result = await loginAccount({
        email: String(form.get("email")),
        password: String(form.get("password")),
      });
      setAuth(result.tokens.access_token, result.tokens.refresh_token, result.user);
      navigate("/dashboard");
    } catch (err) {
      setError(getErrorMessage(err, "Unable to sign in"));
    } finally {
      setPending(false);
    }
  }

  return (
    <AuthCard
      title="Sign in"
      subtitle="Welcome back."
      onSubmit={onSubmit}
      submitLabel="Sign in"
      error={error}
      pending={pending}
      footer={
        <>
          No account?{" "}
          <Link className="font-medium text-teal-700" to="/register">
            Create one
          </Link>
        </>
      }
    >
      <Field label="Email">
        <input name="email" type="email" required className={inputClass} autoComplete="email" />
      </Field>
      <Field label="Password">
        <input
          name="password"
          type="password"
          required
          className={inputClass}
          autoComplete="current-password"
        />
      </Field>
    </AuthCard>
  );
}
