// import { UserInfo, ConversationRequest } from "./models";

// export async function (options: ConversationRequest, abortSignal: AbortSignal): Promise<Response> {
//     const response = await fetch("/conversation", {
//         method: "POST",
//         headers: {
//             "Content-Type": "application/json"
//         },
//         body: JSON.stringify({
//             messages: options.messages
//         }),
//         signal: abortSignal
//     });

//     return response;
// }

// export async function getUserInfo(): Promise<UserInfo[]> {
//     const response = await fetch('/.auth/me');
//     if (!response.ok) {
//         console.log("No identity provider found. Access to chat will be blocked.")
//         return [];
//     }

//     const payload = await response.json();
//     return payload;
// }

import { UserInfo, ConversationRequest } from "./models";

// export async function getUserToken(): Promise<UserInfo[]> {
//     const response = await fetch('/.auth/me');
//     if (!response.ok) {
//         console.log("No identity provider found. Access to chat will be blocked.")
//         return [];
//     }

//     const payload = await response.json();
//     const accessToken = payload[0].access_token;
//     if (!accessToken) {
//         console.log("No access token found. Access to chat will be blocked.")
//         return [];
//     }

//     return accessToken;
// }

export async function conversationApi(options: ConversationRequest, abortSignal: AbortSignal): Promise<Response> {

    const accessToken = await getUserToken();

    const response = await fetch("/conversation", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Cache-Control": "max-age=3600",
            "Authorization": `Bearer ${accessToken}`
        },
        body: JSON.stringify({
            messages: options.messages
        }),
        signal: abortSignal
    });

    return response;
}

export async function getUserInfo(): Promise<UserInfo[]> {
    const response = await fetch('/.auth/me');
    if (!response.ok) {
        console.log("No identity provider found. Access to chat will be blocked.")
        return [];
    }

    const payload = await response.json();
    return payload;
}

export async function getUserToken(): Promise<string> {
    const response = await fetch('/.auth/me');
    if (!response.ok) {
        console.log("No identity provider found. Access to chat will be blocked.")
        return "";
    }

    const payload = await response.json();
    const userInfo = payload[0];
    if (!userInfo) {
        console.log("No user information found. Access to chat will be blocked.")
        return "";
    }

    const accessToken = userInfo.access_token;
    if (!accessToken) {
        console.log("No access token found. Access to chat will be blocked.")
        return "";
    }
    console.log(`Access token: ${accessToken}`);
    return accessToken;
}
