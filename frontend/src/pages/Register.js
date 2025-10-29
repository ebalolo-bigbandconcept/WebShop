import { useState } from "react";
import httpClient from "../components/httpClient";
import { useNavigate } from "react-router-dom";

const Register = ({ setUser }) => {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [first_name, setFirstName] = useState("");
  const [last_name, setLastName] = useState("");
  const [password, setPassword] = useState("");

  const [form_submited, setFormSubmited] = useState(false);
  const [first_name_error, setFirstNameError] = useState("");
  const [last_name_error, setLastNameError] = useState("");
  const [email_error, setEmailError] = useState("");
  const [password_error, setPasswordError] = useState("");


  // ### User input verifications ###
  const firstNameVerif = (value) => {
    if (value === "") {
      setFirstNameError("Veuillez entrer votre prénom");
      return false;
    }
    setFirstNameError("");
    return true;
  };

  const lastNameVerif = (value) => {
    if (value === "") {
      setLastNameError("Veuillez entrer votre nom");
      return false;
    }
    setLastNameError("");
    return true;
  };

  const emailVerif = (value) => {
    if (value === "") {
      setEmailError("Veuillez entrer votre email");
      return false;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(value)) {
      setEmailError("Format d'email invalide");
      return false;
    }
    setEmailError("");
    return true;
  };

  const passwordVerif = (value) => {
    if (value === "") {
      setPasswordError("Veuillez entrer votre mot de passe");
      return false;
    }
    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$/;
    if (!passwordRegex.test(value)) {
      setPasswordError(
        "Le mot de passe doit contenir au moins 8 caractères et doit inclure une majuscule, une minuscule, un chiffre et un caractère spécial."
      );
      return false;
    }
    setPasswordError("");
    return true;
  };

  // ### Register user in ###
  const registerUserIn = async (e) => {
    e.preventDefault();
    setFormSubmited(true);

    const isFirstNameValid = firstNameVerif(first_name);
    const isLastNameValid = lastNameVerif(last_name);
    const isEmailValid = emailVerif(email);
    const isPasswordValid = passwordVerif(password);

    const isFormValid =
      isFirstNameValid && isLastNameValid && isEmailValid && isPasswordValid;

    if (isFormValid) {
      httpClient
        .post(`${process.env.REACT_APP_BACKEND_URL}/user/register`, {
          email: email,
          first_name: first_name,
          last_name: last_name,
          password: password,
        })
        .then((resp) => {
          setUser(resp.data);
          console.log(resp.data);
          navigate("/liste-clients");
        })
        .catch((error) => {
          if (error.response && error.response.data && error.response.data.error) {
            alert(error.response.data.error);
          } else {
            alert("Une erreur est survenue.");
          }
        });
    }
  };

  return (
    <div className="vh-100 d-flex justify-content-center align-items-center">
      <div className="row d-flex justify-content-center align-items-center h-100">
        <div className="col-md-9 col-lg-6 col-xl-5">
          <img src="https://mdbcdn.b-cdn.net/img/Photos/new-templates/bootstrap-login-form/draw2.webp" className="img-fluid" alt="Sample"/>
        </div>
        <div className="col-md-8 col-lg-6 col-xl-4 offset-xl-1">
          <form onSubmit={registerUserIn}>
            <div className="row mb-4">
              <div className="form-outline col-6">
                <label className="form-label">Nom</label>
                <input type="text" value={last_name} onChange={(e) => {setLastName(e.target.value);lastNameVerif(e.target.value);}}
                  className={`form-control form-control-lg ${last_name_error ? "is-invalid" : form_submited ? "is-valid" : ""}`} placeholder="Nom"/>
                <div className="invalid-feedback">{last_name_error}</div>
              </div>
              <div className="form-outline col-6">
                <label className="form-label">Prénom</label>
                <input type="text" value={first_name} onChange={(e) => {setFirstName(e.target.value);firstNameVerif(e.target.value);}}
                  className={`form-control form-control-lg ${first_name_error ? "is-invalid" : form_submited ? "is-valid": ""}`} placeholder="Prénom"/>
                <div className="invalid-feedback">{first_name_error}</div>
              </div>
            </div>
            <div className="form-outline mb-4">
              <label className="form-label">Adresse mail</label>
              <input type="email" value={email} onChange={(e) => {setEmail(e.target.value);emailVerif(e.target.value);}}
                className={`form-control form-control-lg ${email_error ? "is-invalid" : form_submited ? "is-valid" : ""}`} placeholder="example@email.com"/>
              <div className="invalid-feedback">{email_error}</div>
            </div>

            <div className="form-outline mb-3">
              <label className="form-label">Mot de passe</label>
              <input type="password" value={password} onChange={(e) => {setPassword(e.target.value);passwordVerif(e.target.value);}}
                className={`form-control form-control-lg ${password_error ? "is-invalid" : form_submited ? "is-valid" : "" }`} placeholder="Entrer votre mot de passe."/>
              <div className="invalid-feedback">{password_error}</div>
            </div>

            <div className="text-center text-lg-start mt-4 pt-2">
              <button type="submit" className="btn btn-primary btn-lg">Créer un compte</button>
              <p className="small fw-bold mt-2 pt-1 mb-0">Vous avez déjà un compte?<a href="/login" className="link-danger">Se connecter</a></p>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Register;
