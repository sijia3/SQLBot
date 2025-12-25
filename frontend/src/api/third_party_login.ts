import { request } from '@/utils/request'

// 定义参数接口
export interface OAuthLoginParams {
  code: string
  source?: string
}

// 定义返回值接口 (根据后端 Token 模型)
export interface TokenResponse {
  access_token: string
  token_type: string
}

export const ThirdPartyAuthApi = {
  // 第三方 Code 换 Token 接口
  loginByOauth: (data: OAuthLoginParams) => {
    // 【修改点】: 去掉 <any, TokenResponse> 中的 any，只保留返回值类型
    return request.post<TokenResponse>('/login/oauth/callback', data)
  }
}
