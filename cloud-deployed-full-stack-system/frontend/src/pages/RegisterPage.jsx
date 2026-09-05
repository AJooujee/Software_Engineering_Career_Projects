/**
 * Registration page for new Cloud Operations viewer accounts.
 */

import { useState } from "react";
import { Link, useNavigate } from "react-router";

import { useAuth } from "../auth/AuthContext.jsx";


export function RegisterPage() {
  const navigate = useNavigate();
  const { register } = useAuth();

  const [formData, setFormData] = useState({
    fullName: "",
    email: "",
    password: "",
    passwordConfirmation: "",
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

    if (formData.password !== formData.passwordConfirmation) {
      setError("Password confirmation does not match.");
      return;
    }

    setIsSubmitting(true);

    try {
      await register({
        fullName: formData.fullName,
        email: formData.email,
        password: formData.password,
      });

      navigate("/dashboard", {
        replace: true,
      });
    } catch (requestError) {
      setError(
        requestError.message
        ?? "Unable to create the account. Please try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <>
      <div className="auth-card__heading">
        <p className="eyebrow">Create an account</p>
        <h2>Join the operations workspace</h2>
        <p>
          New accounts begin with viewer access.
          An administrator can update your role later.
        </p>
      </div>

      {error && (
        <div className="form-alert form-alert--error" role="alert">
          {error}
        </div>
      )}

      <form className="auth-form" onSubmit={handleSubmit}>
        <label className="form-field">
          <span>Full name</span>
          <input
            type="text"
            name="fullName"
            value={formData.fullName}
            onChange={handleChange}
            autoComplete="name"
            minLength={1}
            maxLength={120}
            required
            autoFocus
          />
        </label>

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
          />
        </label>

        <label className="form-field">
          <span>Password</span>
          <input
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            autoComplete="new-password"
            minLength={12}
            maxLength={128}
            aria-describedby="password-requirements"
            required
          />

          <small id="password-requirements">
            Use between 12 and 128 characters.
          </small>
        </label>

        <label className="form-field">
          <span>Confirm password</span>
          <input
            type="password"
            name="passwordConfirmation"
            value={formData.passwordConfirmation}
            onChange={handleChange}
            autoComplete="new-password"
            minLength={12}
            maxLength={128}
            required
          />
        </label>

        <button
          type="submit"
          className="button-primary button-full-width"
          disabled={isSubmitting}
        >
          {isSubmitting ? "Creating account..." : "Create account"}
        </button>
      </form>

      <p className="auth-card__switch">
        Already registered?{" "}
        <Link to="/login">Sign in</Link>
      </p>
    </>
  );
}
