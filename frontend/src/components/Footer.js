import React from 'react';

function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-light text-center py-3 mt-4">
      <div className="container">
        <span className="text-muted">© {currentYear} Artech Sécurité. Tous droits réservés.</span>
      </div>
    </footer>
  );
}

export default Footer;
