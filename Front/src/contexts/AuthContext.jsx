import React, { createContext, useContext, useState, useEffect } from "react";
import {
  login as apiLogin,
  register as apiRegister,
  logout as apiLogout,
  getProfile,
  isAuthenticated,
} from "../api/api";

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initializeAuth = async () => {
      console.log("Initializing auth...");
      if (isAuthenticated()) {
        console.log("Token found, getting profile...");
        try {
          const response = await getProfile();
          console.log("Profile response:", response);
          if (response.success) {
            setUser(response.user);
            console.log("User set:", response.user);
          } else {
            console.log("Failed to get profile:", response.error);
            // Token might be expired, clear it
            apiLogout();
          }
        } catch (error) {
          console.error("Error initializing auth:", error);
          apiLogout();
        }
      } else {
        console.log("No token found");
      }
      setLoading(false);
    };

    initializeAuth();
  }, []);

  const login = async (credentials) => {
    try {
      console.log("Attempting login...");
      const response = await apiLogin(credentials);
      console.log("Login response in context:", response);

      if (response.success) {
        setUser(response.user);
        console.log("Login successful, user set in context");
        return { success: true };
      } else {
        console.log("Login failed:", response.error);
        return { success: false, error: response.error };
      }
    } catch (error) {
      console.error("Login error in context:", error);
      return { success: false, error: error.message };
    }
  };

  const register = async (userData) => {
    try {
      console.log("Attempting registration...");
      const response = await apiRegister(userData);
      console.log("Registration response:", response);

      if (response.success) {
        console.log("Registration successful, attempting login...");
        // After registration, log the user in
        const loginResult = await login({
          username: userData.username,
          password: userData.password,
        });
        console.log("Auto-login after registration:", loginResult);
        return loginResult;
      } else {
        console.log("Registration failed:", response.error);
        return { success: false, error: response.error };
      }
    } catch (error) {
      console.error("Registration error in context:", error);
      return { success: false, error: error.message };
    }
  };

  const logout = () => {
    console.log("Logging out...");
    apiLogout();
    setUser(null);
  };

  const value = {
    user,
    login,
    register,
    logout,
    loading,
    isAuthenticated: !!user,
  };

  console.log("AuthProvider value:", {
    user: user?.username,
    loading,
    isAuthenticated: !!user,
  });

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
