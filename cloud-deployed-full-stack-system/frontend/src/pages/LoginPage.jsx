/**
 * Sign-in page for existing Cloud Operations users.
 */

import { useState } from "react";
import {
  Link,
  useLocation,
  useNavigate,
} from "react-router";

import { useAuth } from "../auth/AuthContext.jsx";


/**
 * Return a safe internal path requested before authentication.
 */
function getReturnPath(location) {
  const previousLocation = location.state?.from;
  const pathname = previousLocation?.pathname;

  if (
    typeof pathname !== "string"
    || !pathname.startsWith("/")
    || pathname.startsWith("//")
  ) {
    return "/dashboard";
  }

  return [
    pathname,
    previousLocation.search ?? "",
    previousLocation.hash ?? "",
  ].join("");
}


export function LoginPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { login } = useAuth();

  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function handleChange(event) {
    const { name, value } = event.target;

    setFormData((currentFormData) => ({
      ...currentFormData,
      [name]: value,
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await login(formData);

      navigate(getReturnPath(location), {
        replace: true,
      });
    } catch (requestError) {
      setError(
        requestError.message
        ?? "Unable to sign in. Please try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <>
      <div className="auth-card__heading">
        <p className="eyebrow">Welcome back</p>
        <h2>Sign in to your workspace</h2>
        <p>
          Use your Cloud Operations account to continue.
        </p>
      </div>

      {error && (
        <div className="form-alert form-alert--error" role="alert">
          {error}
        </div>
      )}

      <form className="auth-form" onSubmit={handleSubmit}>
        <label className="form-field">
          <span>Email address</span>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            autoComplete="email"
            maxLength={320}
            required
            autoFocus
          />
        </label>

        <label className="form-field">
          <span>Password</span>
          <input
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            autoComplete="current-password"
            required
          />
        </label>

        <button
          type="submit"
          className="button-primary button-full-width"
          disabled={isSubmitting}
        >
          {isSubmitting ? "Signing in..." : "Sign in"}
        </button>
      </form>

      <p className="auth-card__switch">
        Need an account?{" "}
        <Link to="/register">Create one</Link>
      </p>
    </>
  );
}
