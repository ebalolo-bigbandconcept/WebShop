import { useEffect } from "react";
import { useNavigate } from "react-router";

function ConsentComplete() {
  const navigate = useNavigate();

  useEffect(() => {
    // Après consentement, revenir à la page originale
    const redirectPath = sessionStorage.getItem("redirectAfterConsent") || "/";
    navigate(redirectPath + "?consent=ok");
    sessionStorage.removeItem("redirectAfterConsent");
  }, [navigate]);

  return <div>Consentement accordé. Redirection en cours...</div>;
}
export default ConsentComplete;