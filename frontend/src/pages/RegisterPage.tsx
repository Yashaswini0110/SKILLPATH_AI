import { type FormEvent, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { AuthCard, Field, inputClass } from "../components/common/AuthCard";
import { getErrorMessage } from "../services/api";
import { registerAccount } from "../services/auth";
import { useAuthStore } from "../store/authStore";
import type { UserRole } from "../types/api";

const ROLES: UserRole[] = ["EMPLOYEE", "MANAGER", "MENTOR", "HR_ADMIN", "SYSTEM_ADMIN"];

export function RegisterPage() {
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
    const password = String(form.get("password"));
    const hasLetter = /[A-Za-z]/.test(password);
    const hasNumber = /\d/.test(password);
    if (!hasLetter || !hasNumber) {
      setError("Password must contain at least one letter and one number (for example Password1).");
      return;
    }
    setPending(true);
    setError(null);
    try {
      const result = await registerAccount({
        email: String(form.get("email")),
        password,
        full_name: String(form.get("full_name")),
        role: String(form.get("role")) as UserRole,
      });
      setAuth(result.tokens.access_token, result.tokens.refresh_token, result.user);
      navigate("/dashboard");
    } catch (err) {
      setError(getErrorMessage(err, "Unable to register"));
    } finally {
      setPending(false);
    }
  }

  return (
    <AuthCard
      title="Create account"
      subtitle="Password must be at least 8 characters and include a letter and a number."
      onSubmit={onSubmit}
      submitLabel="Create account"
      error={error}
      pending={pending}
      footer={
        <>
          Already registered?{" "}
          <Link className="font-medium text-teal-700" to="/login">
            Sign in
          </Link>
        </>
      }
    >
      <Field label="Full name">
        <input name="full_name" required className={inputClass} autoComplete="name" />
      </Field>
      <Field label="Email">
        <input name="email" type="email" required className={inputClass} autoComplete="email" />
      </Field>
      <Field label="Password">
        <input
          name="password"
          type="password"
          required
          minLength={8}
          pattern="(?=.*[A-Za-z])(?=.*\d).{8,}"
          title="At least 8 characters, including a letter and a number"
          className={inputClass}
          autoComplete="new-password"
        />
      </Field>
      <Field label="Application role">
        <select name="role" className={inputClass} defaultValue="EMPLOYEE">
          {ROLES.map((role) => (
            <option key={role} value={role}>
              {role}
            </option>
          ))}
        </select>
      </Field>
    </AuthCard>
  );
}
