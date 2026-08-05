import { AuthResponseDto, ApiUser, RefreshResponseDto } from '@/types/api';
import { AuthResult, AuthSession } from '@/types/auth';
import { User } from '@/types/user';

export function mapApiUser(dto: ApiUser): User {
  return {
    id: dto.id,
    email: dto.email,
    displayName: dto.display_name,
    isActive: dto.is_active,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at,
  };
}

export function mapTokenResponse(dto: RefreshResponseDto): AuthSession {
  if (dto.token_type.toLowerCase() !== 'bearer') {
    throw new Error('服务器返回了不支持的 Token 类型。');
  }

  return {
    accessToken: dto.access_token,
    refreshToken: dto.refresh_token,
    tokenType: 'bearer',
    expiresIn: dto.expires_in,
  };
}

export function mapAuthResponse(dto: AuthResponseDto): AuthResult {
  return {
    user: mapApiUser(dto.user),
    session: mapTokenResponse(dto),
  };
}
