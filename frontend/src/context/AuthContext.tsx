import React, {
  createContext,
  useState,
  useContext,
  ReactNode,
  Dispatch,
  SetStateAction,
  useEffect,
} from 'react';

interface AuthContextType {
  isLoggedIn: boolean;
  userId: string;
  tipoUsuario: string;
  nomeUsuario: string;
  token: string;
  setAuthData: Dispatch<SetStateAction<{
    isLoggedIn: boolean;
    userId: string;
    tipoUsuario: string;
    nomeUsuario: string;
    token: string;
  }>>;
}

const defaultAuthContext: AuthContextType = {
  isLoggedIn: false,
  userId: '',
  tipoUsuario: '',
  nomeUsuario: '',
  token: '',
  setAuthData: () => undefined,
};

const AuthContext = createContext<AuthContextType>(defaultAuthContext);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [authData, setAuthData] = useState<{
    isLoggedIn: boolean;
    userId: string;
    tipoUsuario: string;
    nomeUsuario: string;
    token: string;
  }>({
    isLoggedIn: false,
    userId: '',
    tipoUsuario: '',
    nomeUsuario: '',
    token: '',
  });

  useEffect(() => {
    const storedAuth = localStorage.getItem('authData');
    if (storedAuth) {
      const parsedAuth = JSON.parse(storedAuth);
      if (parsedAuth.isLoggedIn && (!parsedAuth.token || !parsedAuth.userId)) {
        localStorage.removeItem('authData');
        return;
      }
      setAuthData(parsedAuth);
    }
  }, []);

  useEffect(() => {
    if (authData.isLoggedIn) {
      localStorage.setItem('authData', JSON.stringify(authData));
    } else {
      localStorage.removeItem('authData');
    }
  }, [authData]);

  return (
    <AuthContext.Provider value={{ ...authData, setAuthData }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  return useContext(AuthContext);
};
