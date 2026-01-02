import { useParams } from "react-router";
import { useNavigate } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import httpClient from "../components/httpClient";
import Modal from "../components/Modal";
import { useToast } from "../components/Toast";

function ManageUser() {
  const user_id = useParams();
  const navigate = useNavigate();

  const [user, setUser] = useState();

  const [new_prenom, setNewFirstName] = useState(null);
  const [new_nom, setNewLastName] = useState(null);
  const [new_email, setNewEmail] = useState(null);
  const [new_password, setNewPassword] = useState(null);
  const [new_role, setNewRole] = useState(null);

  const [form_submited, setFormSubmited] = useState(false);
  const [first_name_error, setFirstNameError] = useState("");
  const [last_name_error, setLastNameError] = useState("");
  const [email_error, setEmailError] = useState("");
  const [password_error, setPasswordError] = useState("");
  const [role_error, setRoleError] = useState("");

  // Set modal to modify or delete mode
  const [MODIFY, setMODIFY] = useState(false);
  const [DELETE, setDELETE] = useState(false);

  const { showToast } = useToast();

  const modalRef = useRef(null);
  const showModal = () => {
    modalRef.current && modalRef.current.open();
  };

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
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(value)) {
      setEmailError("Format d'email invalide");
      return false;
    }
    setEmailError("");
    return true;
  };

  const passwordVerif = (value) => {
    if (value) {
      // Only check mdp if it's provided
      const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$/;
      if (!passwordRegex.test(value)) {
        setPasswordError(
          "Le mot de passe doit contenir au moins 8 caractères et doit inclure une majuscule, une minuscule, un chiffre et un caractère spécial."
        );
        return false;
      }
    }
    setPasswordError("");
    return true;
  };

  // ### Modify account ###
  const modify_account = async (e) => {
    e.preventDefault();
    setFormSubmited(true);

    const isFirstNameValid = firstNameVerif(new_prenom);
    const isLastNameValid = lastNameVerif(new_nom);
    const isEmailValid = emailVerif(new_email);
    const isPasswordValid = passwordVerif(new_password);

    const isFormValid =
      isFirstNameValid && isLastNameValid && isEmailValid && isPasswordValid;
    if (isFormValid) {
      const payload = {
        prenom: new_prenom ?? user.prenom,
        nom: new_nom ?? user.nom,
        email: new_email ?? user.email,
        role: new_role ?? user.role,
      };

      if (new_password) {
        payload.mdp = new_password;
      } else {
        payload.mdp = user.mdp;
      }

      httpClient
        .post(`${process.env.REACT_APP_BACKEND_URL}/admin/update-user/${user_id.id}`, payload, {
          headers: {"Content-Type": "application/json"},
        })
        .then((resp) => {
          showToast({ message: "Utilisateur modifié avec succès", variant: "success" });
          navigate("/admin/dashboard");
        })
        .catch((error) => {
          if (error.response && error.response.data && error.response.data.error) {
            if (error.response.data.error === "Impossible de modifier le rôle du dernier compte administrateur.") {
              setRoleError("Impossible de modifier le rôle du dernier compte administrateur.");
            }else if (error.response.data.error === "Impossible de modifier votre propre rôle administrateur.") {
              setRoleError("Impossible de modifier votre propre rôle administrateur.");
            }else if (error.response.status === 409){
              setEmailError(error.response.data.error)
            }else{
              showToast({ message: error.response.data.error, variant: "danger" });
            }
          } else {
            showToast({ message: "Une erreur est survenue.", variant: "danger" });
          }
        });
    }
  };

  // ### Delete account ###
  const delete_account = async () => {
    setFormSubmited(true);
    httpClient
      .post(`${process.env.REACT_APP_BACKEND_URL}/admin/delete-user/${user_id.id}`)
      .then((resp) => {
        showToast({ message: "Utilisateur supprimé avec succès", variant: "success" });
        navigate("/admin/dashboard");
      })
      .catch((error) => {
        if (error.response && error.response.data && error.response.data.error) {
          showToast({ message: error.response.data.error, variant: "danger" });
          if (error.response.data.error === "Vous ne pouvez pas supprimer votre propre compte admin.") {
            navigate("/admin/dashboard");
          }
        } else {
          showToast({ message: "Une erreur est survenue.", variant: "danger" });
        }
      });
  };

  // ### Handle modal close ###
  const handle_close = async () => {
    modalRef.current && modalRef.current.close();
    setDELETE(false);
    setMODIFY(false);
  };

  // ### Fetch user info on page load ###
  useEffect(() => {
    httpClient
      .post(`${process.env.REACT_APP_BACKEND_URL}/admin/info-user/${user_id.id}`)
      .then((resp) => {
        setUser(resp.data);
      })
      .catch((error) => {
        if (error.response && error.response.data && error.response.data.error) {
          showToast({ message: error.response.data.error, variant: "danger" });
        } else {
          showToast({ message: "Une erreur est survenue.", variant: "danger" });
        }
      });
  }, [user_id.id]);

  // ### Pre-fill form with current user info ###
  useEffect(() => {
    if (user) {
      setNewFirstName(user.prenom);
      setNewLastName(user.nom);
      setNewEmail(user.email);
      setNewRole(user.role);
    }
  }, [user]);

  return (
    <div>
      {user !== undefined ? (
        <div className="">
          <h1>Modifier les informations de {user.prenom} {user.nom}</h1>
          <form className="row mt-4">
            <div className="form-outline col-4">
              <label className="form-label">Nom</label>
              <input type="text" id="nom" value={new_nom} onChange={(e) => {setNewLastName(e.target.value);lastNameVerif(e.target.value);}}
                className={`form-control form-control-lg ${last_name_error ? "is-invalid" : form_submited ? "is-valid" : ""}`} placeholder="Entrer un nouveau nom"
              />
              <div className="invalid-feedback">{last_name_error}</div>
            </div>
            <div className="form-outline col-4">
              <label className="form-label">Prénom</label>
              <input type="text" id="prénom" value={new_prenom} onChange={(e) => {setNewFirstName(e.target.value);firstNameVerif(e.target.value);}}
                className={`form-control form-control-lg ${first_name_error ? "is-invalid" : form_submited ? "is-valid" : ""}`} placeholder="Entrer un nouveau prénom"
              />
              <div className="invalid-feedback">{first_name_error}</div>
            </div>
            <div className="form-outline col-4">
              <label className="form-label">Rôle</label>
              <select value={new_role} onChange={(e) => setNewRole(e.target.value)}
                className={`form-control form-control-lg ${role_error ? "is-invalid" : form_submited ? "is-valid" : ""}`}>
                <option value="Utilisateur">Utilisateur</option>
                <option value="Administrateur">Administrateur</option>
              </select>
              <div className="invalid-feedback">{role_error}</div>
            </div>
            <div className="form-outline mb-4">
              <label className="form-label">Adresse mail</label>
              <input type="email" id="email" value={new_email}onChange={(e) => {setNewEmail(e.target.value);emailVerif(e.target.value);}}
                className={`form-control form-control-lg ${email_error ? "is-invalid" : form_submited ? "is-valid" : ""}`} placeholder="Entrer une nouvelle adresse mail"
              />
              <div className="invalid-feedback">{email_error}</div>
            </div>

            <div className="form-outline mb-3">
              <label className="form-label">Mot de passe</label>
              <input type="password" id="mdp" value={new_password} onChange={(e) => {setNewPassword(e.target.value);passwordVerif(e.target.value);}}
                className={`form-control form-control-lg ${password_error ? "is-invalid" : form_submited ? "is-valid" : ""}`} placeholder="Entrer un nouveau mot de passe"
              />
              <div className="invalid-feedback">{password_error}</div>
            </div>

            <div className="text-center text-lg-start mt-4 pt-2">
              <div className="d-flex justify-content-between">
                <button type="button" onClick={(e) => { setMODIFY(true); setDELETE(false); showModal(); }} className="btn btn-primary btn-lg">Modifier le compte</button>
                <button type="button" onClick={(e) => { setDELETE(true); setMODIFY(false); showModal(); }} className="btn btn-danger btn-lg"> Supprimer le compte</button>
              </div>
              <Modal
                ref={modalRef}
                title={"Attention !"}
                size=""
                backdrop="static"
                keyboard={false}
                footer={(
                  MODIFY ? (
                    <div className="d-flex justify-content-between w-100">
                      <button type="button" className="btn btn-danger" onClick={handle_close}>Non</button>
                      <button type="button" className="btn btn-primary" onClick={modify_account}>Oui</button>
                    </div>
                  ) : DELETE ? (
                    <div className="d-flex justify-content-between w-100">
                      <button type="button" className="btn btn-danger" onClick={handle_close}>Non</button>
                      <button type="button" className="btn btn-primary" onClick={delete_account}>Oui</button>
                    </div>
                  ) : null
                )}
              >
                {MODIFY
                  ? `Êtes vous sur de vouloir modifier le compte de ${user.prenom} ${user.nom} ?`
                  : DELETE
                  ? `Êtes vous sur de vouloir supprimer le compte de ${user.prenom} ${user.nom} ?`
                  : ""}
              </Modal>
            </div>
          </form>
        </div>
      ) : (
        <div>Chargement...</div>
      )}
    </div>
  );
}

export default ManageUser;
