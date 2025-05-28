import React, { useState, useEffect } from "react";
import { hello } from "../api/api";

const HomePage = () => {
  const [msg, setMsg] = useState("No Msg");

  const helloCall = async () => {
    try {
      const response = await hello(); 
      if (response.data.success) {
        setMsg(response.data.message);
      } else {
        setMsg("error occurred");
      }
    } catch (err) {
      console.error("API error:", err);
      setMsg("error occurred");
    }
  };

  useEffect(() => {
    helloCall();
  }, []);

  return (
    <>
      <h1>Home Page</h1>
      <h3>{msg}</h3>
    </>
  );
};

export default HomePage;
