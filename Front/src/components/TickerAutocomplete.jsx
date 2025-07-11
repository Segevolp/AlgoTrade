import React from "react";
import { Autocomplete, TextField, Chip } from "@mui/material";

// Popular tickers list
const POPULAR_TICKERS = [
  // Major Indices
  "^GSPC",
  "^DJI",
  "^IXIC",
  "^RUT",
  "^VIX",

  // Tech Giants
  "AAPL",
  "MSFT",
  "GOOGL",
  "GOOG",
  "AMZN",
  "TSLA",
  "META",
  "NFLX",
  "NVDA",
  "ORCL",

  // Finance
  "JPM",
  "BAC",
  "WFC",
  "C",
  "GS",
  "MS",
  "AXP",
  "V",
  "MA",
  "PYPL",

  // Healthcare
  "JNJ",
  "PFE",
  "UNH",
  "ABBV",
  "MRK",
  "TMO",
  "ABT",
  "DHR",
  "BMY",
  "AMGN",

  // Consumer
  "KO",
  "PEP",
  "WMT",
  "PG",
  "DIS",
  "NKE",
  "MCD",
  "SBUX",
  "HD",
  "LOW",

  // Energy
  "XOM",
  "CVX",
  "COP",
  "SLB",
  "MPC",
  "VLO",
  "OXY",
  "EOG",
  "KMI",
  "WMB",

  // ETFs
  "SPY",
  "QQQ",
  "IWM",
  "VTI",
  "VOO",
  "VEA",
  "VWO",
  "GLD",
  "SLV",
  "TLT",

  // Crypto ETFs
  "BITO",
  "COIN",

  // Commodities
  "GLD",
  "SLV",
  "USO",
  "UNG",
  "DBA",
  "CORN",
  "SOYB",
  "WEAT",

  // International
  "BABA",
  "TSM",
  "ASML",
  "SAP",
  "UL",
  "NVO",
  "SHOP",
  "SE",
  "MELI",

  // Bonds
  "^TNX",
  "TLT",
  "IEF",
  "SHY",
  "HYG",
  "LQD",
  "VMOT",
  "BND",

  // Additional Popular Stocks
  "INTC",
  "AMD",
  "CRM",
  "ADBE",
  "QCOM",
  "CSCO",
  "IBM",
  "TXN",
  "AVGO",
  "F",
  "GM",
  "RIVN",
  "LCID",
  "NIO",
  "XPEV",
  "LI",
  "RBLX",
  "ROKU",
  "SNAP",
  "TWTR",
  "PINS",
  "UBER",
  "LYFT",
  "ABNB",
  "SQ",
  "HOOD",
  "SOFI",
  "AFRM",
  "UPST",
  "PLTR",
  "SNOW",
  "DDOG",
  "ZM",
  "DOCU",
  "WORK",
  "TEAM",
  "OKTA",
  "CRWD",
  "NET",
  "FSLY",
  "SPOT",
  "TWLO",
  "SHOP",
  "ETSY",
  "EBAY",
  "AMZN",
  "BKNG",
  "EXPE",
].sort();

const TickerAutocomplete = ({
  value,
  onChange,
  name,
  label = "Ticker Symbol",
  placeholder = "e.g., AAPL, GOOGL, ^GSPC",
  multiple = false,
  freeSolo = true,
  fullWidth = true,
  error = false,
  helperText = "",
  disabled = false,
  required = false,
  variant = "outlined",
  size = "medium",
  ...props
}) => {
  const handleChange = (event, newValue) => {
    if (multiple) {
      // For multiple selection, newValue is an array
      onChange({ target: { name, value: newValue } });
    } else {
      // For single selection, newValue is a string or null
      onChange({ target: { name, value: newValue || "" } });
    }
  };

  const renderTags = (tagValue, getTagProps) => {
    return tagValue.map((option, index) => (
      <Chip
        variant="outlined"
        label={option}
        {...getTagProps({ index })}
        key={index}
        size="small"
      />
    ));
  };

  return (
    <Autocomplete
      options={POPULAR_TICKERS}
      value={value}
      onChange={handleChange}
      multiple={multiple}
      freeSolo={freeSolo}
      disableCloseOnSelect={multiple}
      renderTags={multiple ? renderTags : undefined}
      sx={{
        minWidth: fullWidth ? "100%" : "320px",
        "& .MuiInputBase-root": {
          minWidth: "320px",
        },
      }}
      renderInput={(params) => (
        <TextField
          {...params}
          label={label}
          placeholder={placeholder}
          fullWidth={fullWidth}
          error={error}
          helperText={helperText}
          disabled={disabled}
          required={required}
          variant={variant}
          size={size}
          InputProps={{
            ...params.InputProps,
            style: {
              textTransform: "uppercase",
              minWidth: "320px",
            },
          }}
        />
      )}
      renderOption={(props, option) => (
        <li {...props} key={option}>
          <strong>{option}</strong>
        </li>
      )}
      filterOptions={(options, { inputValue }) => {
        const filtered = options.filter((option) =>
          option.toLowerCase().includes(inputValue.toLowerCase())
        );

        // If the input doesn't match any existing options and freeSolo is true,
        // show the input as an option
        if (
          freeSolo &&
          inputValue !== "" &&
          !filtered.includes(inputValue.toUpperCase())
        ) {
          filtered.push(inputValue.toUpperCase());
        }

        return filtered;
      }}
      getOptionLabel={(option) => option}
      isOptionEqualToValue={(option, value) => option === value}
      {...props}
    />
  );
};

export default TickerAutocomplete;
