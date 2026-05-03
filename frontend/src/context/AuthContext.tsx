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
  tipoUsuario: string;
  nomeUsuario: string;
  token: string;
  setAuthData: Dispatch<SetStateAction<{
    isLoggedIn: boolean;
    tipoUsuario: string;
    nomeUsuario: string;
    token: string;
  }>>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [authData, setAuthData] = useState<{
    isLoggedIn: boolean;
    tipoUsuario: string;
    nomeUsuario: string;
    token: string;
  }>({
    isLoggedIn: false,
    tipoUsuario: '',
    nomeUsuario: '',
    token: '',
  });

  useEffect(() => {
    const storedAuth = localStorage.getItem('authData');
    if (storedAuth) {
      const parsedAuth = JSON.parse(storedAuth);
      if (parsedAuth.isLoggedIn && !parsedAuth.token) {
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
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
