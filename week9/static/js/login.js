// 取得相關 DOM 元素
const popUpArea = document.getElementById("pop-up-area");
const signInForm = document.getElementById("signInForm");
const signUpForm = document.getElementById("signUpForm");
const signUpLink = document.getElementById("signUpLink"); // 註冊連結
const signInLink = document.getElementById("signInLink"); // 登入連結
const closeSignUpForm = document.getElementById("closeSignUpForm");

console.log("closeSignUpForm是：", closeSignUpForm); // 確保這裡可以顯示正確的元素

// 切換到註冊表單
signUpLink.addEventListener("click", (event) => {
  event.preventDefault(); // 防止連結跳轉
  signInForm.style.display = "none";
  signUpForm.style.display = "block";
});

// 切換到登入表單
signInLink.addEventListener("click", (event) => {
  event.preventDefault(); // 防止連結跳轉
  signUpForm.style.display = "none";
  signInForm.style.display = "block";
});

// 關閉註冊表單
closeSignUpForm.addEventListener("click", () => {
  popUpArea.style.display = "none"; // 隱藏黑色遮罩
  signUpFormContainer.style.display = "none"; // 隱藏註冊表單
});

// 當使用者進入頁面時顯示註冊表單（如果需要）
popUpArea.style.display = "none";
signUpFormContainer.style.display = "none";

document.querySelector(".sign-in").addEventListener("click", () => {
  signUpFormContainer.style.display = "block"; // 顯示註冊表單
  popUpArea.style.display = "block"; // 顯示黑色遮罩
});

// 抓取註冊表單資料
signUpForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const name = document.querySelector("#signup_username").value.trim();
  const email = document.querySelector("#signup_email").value.trim();
  const password = document.querySelector("#signup_password").value.trim();

  try {
    const response = await fetch("/api/user", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        name: name,
        email: email,
        password: password,
      }),
    });

    const data = await response.json();
    if (!data.ok) {
      showMessage(data.message, "error", "signup");
      return;
    }
    showMessage(data.message, "success", "signup");
  } catch (error) {
    showMessage("無法連接伺服器，請稍後再試！", "error", "signup");
  }
});

// 抓取登入表單資料
signInForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const email = document.getElementById("signin_email").value.trim();
  const password = document.getElementById("signin_password").value.trim();

  if (!signin_email || !signin_password) {
    showMessage("請填寫所有欄位！", "error", "signin");
    return;
  }
  try {
    const response = await fetch("/api/user/auth", {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email: email,
        password: password,
      }),
    });

    const data = await response.json();
    console.log("登入回應:", data); // 確認回傳的資料

    // 檢查回應狀態碼，若非成功（2xx範圍），則顯示錯誤訊息
    if (!response.ok) {
      showMessage(data.message, "error", "signin");
      return;
    }
    localStorage.setItem("token", data.token);
    showMessage("登入成功！", "success", "signin");

    // 延遲一點點再關閉視窗，讓使用者看到成功訊息
    setTimeout(() => {
      popUpArea.style.display = "none"; // 隱藏黑色遮罩
      signUpFormContainer.style.display = "none"; // 隱藏登入表單
      location.reload(); // 重新載入頁面以更新狀態
    }, 1000);
  } catch (error) {
    console.log("錯誤訊息", error);
    showMessage("無法連接伺服器，請稍後再試！", "error", "signin");
  }
});

// 取得當前登入的會員資訊
document.addEventListener("DOMContentLoaded", async () => {
  const token = localStorage.getItem("token");
  console.log("token:", token); // 確認 token 是否存在

  try {
    const response = await fetch("/api/user/auth", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer " + token,
      },
    });

    // 注意這行也可能會拋錯（如果回傳不是 JSON）
    const responseData = await response.json();

    if (!responseData.data) {
      alert("驗證失敗，請重新登入！");
      localStorage.clear();
      return;
    }

    // 驗證成功後的流程
    const signInBtn = document.querySelector(".sign-in");
    signInBtn.textContent = "登出";

    signInBtn.addEventListener("click", async () => {
      popUpArea.style.display = "none";
      signUpFormContainer.style.display = "none";
      localStorage.removeItem("token");
      window.location.reload();
    });
  } catch (error) {
    alert("驗證會員時出現錯誤，請稍後再試！");
    console.error("驗證會員時出現錯誤：", error);
    localStorage.clear();
    // location.reload(); // 強制刷新，避免進入不該看的頁面
  }
});

function showMessage(message, type, formType) {
  let messageElement;

  if (formType === "signin") {
    messageElement = document.getElementById("message_signin");
  } else if (formType === "signup") {
    messageElement = document.getElementById("message_signup");
  }
  if (messageElement) {
    messageElement.textContent = message;
    messageElement.style.display = "block"; // 顯示錯誤訊息
    messageElement.style.color = type === "error" ? "red" : "green";
  }
}
